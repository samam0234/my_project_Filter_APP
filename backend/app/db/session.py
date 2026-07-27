"""Engine / session factory. SQLite (local) or MariaDB (prod/docker)."""

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
    """Ensure SQLite file parent directory exists; return usable URL."""
    if not url.startswith("sqlite"):
        return url
    if url in {"sqlite://", "sqlite:///:memory:", "sqlite:///:memory"}:
        return "sqlite:///:memory:"

    # forms: sqlite:///relative/path.db  or  sqlite:////absolute/path.db
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

    logger.info("DB engine ready dialect={} url_scheme={}", eng.dialect.name, url.split(":")[0])
    return eng


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session."""
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they do not exist (Phase 1 scaffold; Alembic optional later)."""
    import app.models  # noqa: F401 — register metadata

    eng = get_engine()
    SessionLocal.configure(bind=eng)
    Base.metadata.create_all(bind=eng)
    logger.info("DB tables ensured dialect={}", eng.dialect.name)
