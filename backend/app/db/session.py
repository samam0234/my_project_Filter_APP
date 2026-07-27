"""엔진/세션 팩토리. 로컬 SQLite 또는 배포 MariaDB."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

_engine: Optional[Engine] = None
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
        path = settings.resolve_path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def _build_engine() -> Engine:
    settings = get_settings()
    url = _normalize_sqlite_url(settings.database_url)
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
        def _sqlite_on_connect(dbapi_conn, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("DB 엔진 준비됨 dialect={} url_scheme={}", eng.dialect.name, url.split(":")[0])
    return eng


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: DB 세션을 yield."""
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """테이블이 없으면 생성 (Phase 1; 이후 Alembic 선택)."""
    import app.models  # noqa: F401 — 메타데이터 등록

    eng = get_engine()
    SessionLocal.configure(bind=eng)
    Base.metadata.create_all(bind=eng)
    logger.info("DB 테이블 확인/생성 완료 dialect={}", eng.dialect.name)
