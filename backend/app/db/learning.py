"""학습 데이터 DB — 서비스 DB(app.db.session)와 분리된 두 번째 엔진.

서비스 DB (SQLite): users · auth_sessions · auth_codes · jobs · batch_jobs
학습 DB (MariaDB) : feedbacks · learning_samples

- get_learning_engine() : 학습 DB Engine 싱글톤
- get_learning_db()     : FastAPI Depends 용 세션 generator
- learning_session()    : 라우터 밖(파이프라인 노드·스크립트)용 컨텍스트 매니저
- init_learning_db()    : 접속 확인 → (실패 시 SQLite fallback) → create_all

두 DB 사이에는 FK 가 없다. 피드백은 job_id·user_id 를 값으로만 들고 있고,
파일 사이드카(data/feedback/*.json)가 원본이라 학습 DB 저장이 실패해도 기동 시 동기화로 복구된다.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class LearningBase(DeclarativeBase):
    """학습 DB 테이블 공통 ORM 베이스 (서비스 DB 의 Base 와 메타데이터 분리)."""

    pass


_engine: Optional[Engine] = None
# "mariadb" | "sqlite" | "sqlite(fallback)" — /health · 기동 로그 표시용
_mode: Optional[str] = None
LearningSessionLocal: sessionmaker[Session] = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def _make_engine(url: str, settings: Settings) -> Engine:
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    eng = create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=bool(settings.debug and settings.db_echo),
    )
    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _sqlite_on_connect(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return eng


def _connect_or_fallback(settings: Settings) -> tuple[Engine, str]:
    """설정된 학습 DB 에 접속. MariaDB 가 꺼져 있으면 (허용 시) 로컬 SQLite 로 대체."""
    url = settings.learning_database_url
    eng = _make_engine(url, settings)
    if url.startswith("sqlite"):
        return eng, "sqlite"
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng, eng.dialect.name
    except Exception as exc:
        eng.dispose()
        if not settings.learning_db_fallback_sqlite:
            raise
        logger.warning(
            "학습 DB({}) 접속 실패 → 로컬 SQLite 로 대체 {} : {} "
            "(MariaDB 를 켜고 재기동하면 사이드카 파일에서 다시 동기화됨)",
            eng.dialect.name,
            settings.learning_sqlite_path,
            str(exc).splitlines()[0][:200],
        )
        return _make_engine(settings.learning_sqlite_url, settings), "sqlite(fallback)"


def get_learning_engine() -> Engine:
    global _engine, _mode
    if _engine is None:
        _engine, _mode = _connect_or_fallback(get_settings())
        LearningSessionLocal.configure(bind=_engine)
        logger.info("학습 DB 엔진 준비됨 mode={}", _mode)
    return _engine


def learning_db_mode() -> Optional[str]:
    """현재 학습 DB 모드 (엔진 생성 전이면 None)."""
    return _mode


def get_learning_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: 학습 DB 세션."""
    get_learning_engine()
    db = LearningSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def learning_session() -> Iterator[Session]:
    """라우터 밖에서 쓰는 학습 DB 세션 (예외 시 rollback)."""
    get_learning_engine()
    db = LearningSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _retire_legacy_feedbacks(eng: Engine) -> None:
    """분리 전 스키마의 feedbacks(jobs FK, prompt 컬럼 없음)가 같은 DB 에 있으면 이름을 바꿔 보존.

    예전 Docker 는 서비스 테이블 전체를 MariaDB 에 만들었다. create_all 은 기존 테이블을 고치지 않으므로
    그대로 두면 새 컬럼 insert 가 실패한다. 내용은 사이드카에서 다시 적재된다.
    """
    insp = inspect(eng)
    if not insp.has_table("feedbacks"):
        return
    if "prompt" in {c["name"] for c in insp.get_columns("feedbacks")}:
        return
    legacy = "feedbacks_legacy"
    n = 1
    while insp.has_table(legacy):
        n += 1
        legacy = f"feedbacks_legacy{n}"
    with eng.begin() as conn:
        conn.execute(text(f"ALTER TABLE feedbacks RENAME TO {legacy}"))
    logger.warning("분리 전 feedbacks 테이블을 {} 로 보존 (사이드카에서 다시 적재)", legacy)


def init_learning_db() -> str:
    """학습 DB 테이블 생성. 반환: 모드 문자열."""
    import app.models.learning  # noqa: F401 — 메타데이터 등록

    eng = get_learning_engine()
    _retire_legacy_feedbacks(eng)
    LearningBase.metadata.create_all(bind=eng)
    logger.info("학습 DB 테이블 확인/생성 완료 mode={}", _mode)
    return _mode or eng.dialect.name


def reset_learning_engine() -> None:
    """테스트·설정 변경용: 엔진 싱글톤 초기화."""
    global _engine, _mode
    if _engine is not None:
        _engine.dispose()
    _engine, _mode = None, None
