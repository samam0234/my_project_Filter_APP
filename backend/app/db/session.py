"""엔진/세션 팩토리. 로컬 SQLite 또는 배포 MariaDB.

- get_engine()  : 프로세스 전역 Engine 싱글톤
- get_db()      : FastAPI Depends 용 세션 generator
- init_db()     : create_all (Phase 1; 이후 Alembic 선택)
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

_engine: Optional[Engine] = None
# bind 는 get_engine / init_db 시점에 주입
SessionLocal: sessionmaker[Session] = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def _normalize_sqlite_url(url: str) -> str:
    """SQLite 파일 상위 디렉터리를 만들고 사용 가능한 URL을 반환."""
    if not url.startswith("sqlite"):
        return url
    if url in {"sqlite://", "sqlite:///:memory:", "sqlite:///:memory"}:
        return "sqlite:///:memory:"

    # 형식: sqlite:///상대경로.db 또는 sqlite:////절대경로.db
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    raw = url[len(prefix) :]
    if raw == ":memory:":
        return "sqlite:///:memory:"

    settings = get_settings()
    path = Path(raw)
    if not path.is_absolute():
        path = settings.resolve_runtime_path(raw)
    # 파일이 없어도 상위 폴더는 미리 생성
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def _build_engine() -> Engine:
    """Settings.database_url 로 Engine 생성.

    SQLite: check_same_thread=False + FK PRAGMA ON
    MariaDB: pool_pre_ping 으로 끊긴 연결 감지
    """
    settings = get_settings()
    url = _normalize_sqlite_url(settings.database_url)
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # FastAPI 멀티 스레드에서 동일 연결 사용 허용
        connect_args["check_same_thread"] = False

    eng = create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=bool(settings.debug and settings.db_echo),
    )

    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _sqlite_on_connect(dbapi_conn, _connection_record) -> None:  # type: ignore[no-untyped-def]
            # SQLite 기본 FK 비활성 → 명시 ON
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("DB 엔진 준비됨 dialect={} url_scheme={}", eng.dialect.name, url.split(":")[0])
    return eng


def get_engine() -> Engine:
    """지연 생성 Engine 싱글톤."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: 요청마다 세션을 yield 하고 종료 시 close."""
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# create_all 은 기존 테이블에 컬럼을 추가하지 않는다 → 필요한 컬럼만 ALTER 로 보강.
# (테이블, 컬럼, DDL 타입) — Alembic 도입 전까지의 최소 마이그레이션
_ADDED_COLUMNS: list[tuple[str, str, str]] = [
    ("jobs", "user_id", "VARCHAR(32)"),
]


def _ensure_columns(eng: Engine) -> None:
    """기존 DB 에 없는 컬럼을 NULL 허용으로 추가 (SQLite · MariaDB 공통 문법)."""
    insp = inspect(eng)
    for table, column, ddl in _ADDED_COLUMNS:
        if not insp.has_table(table):
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        if column in existing:
            continue
        with eng.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl} NULL"))
        logger.info("DB 컬럼 추가 {}.{}", table, column)


def init_db() -> None:
    """테이블이 없으면 생성하고, 기존 테이블에 빠진 컬럼을 보강한다 (이후 Alembic 선택)."""
    import app.models  # noqa: F401 — 메타데이터 등록

    eng = get_engine()
    SessionLocal.configure(bind=eng)
    Base.metadata.create_all(bind=eng)
    _ensure_columns(eng)
    logger.info("DB 테이블 확인/생성 완료 dialect={}", eng.dialect.name)
