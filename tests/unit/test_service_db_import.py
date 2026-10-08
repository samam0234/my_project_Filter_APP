# -*- coding: utf-8 -*-
"""서비스 DB 를 SQLite → 다른 DB(운영은 MariaDB)로 옮기기 — app/db/sqlite_import.py."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine, func, select

import app.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base
from app.db.sqlite_import import auto_import, import_sqlite


def _old_sqlite(path):
    """예전 서비스 DB 처럼 kind · terms_agreed_at 열이 없는 SQLite."""
    eng = create_engine(f"sqlite:///{path.as_posix()}")
    Base.metadata.create_all(eng)
    eng.dispose()
    con = sqlite3.connect(path)
    con.execute("insert into users (id, username, email, password_hash, failed_logins, created_at, updated_at) "
                "values ('u1', 'admin', 'admin@example.com', 'h', 0, '2026-10-07 18:28:33', '2026-10-07 18:28:33')")
    con.execute("insert into jobs (id, user_id, prompt, status, quality_score, feedback_saved, parsed_prompt, created_at, updated_at) "
                "values ('j1', 'u1', '사람만 남기고 배경 제거', 'ok', 0.8, 0, '{\"target\": [\"person\"]}', '2026-10-08 01:00:00', '2026-10-08 01:00:00')")
    con.commit()
    con.close()


def test_import_copies_rows_once_and_keeps_json(tmp_path):
    src = tmp_path / "old.db"
    _old_sqlite(src)
    target = create_engine(f"sqlite:///{(tmp_path / 'new.db').as_posix()}")
    first = import_sqlite(src, target)
    assert first["users"] == 1 and first["jobs"] == 1
    assert import_sqlite(src, target) == {"users": 0, "auth_sessions": 0, "auth_codes": 0, "jobs": 0, "batch_jobs": 0}  # 두 번 돌려도 안전
    with target.connect() as conn:
        job = conn.execute(select(Base.metadata.tables["jobs"])).mappings().one()
    assert job["parsed_prompt"] == {"target": ["person"]} and job["user_id"] == "u1"


def test_auto_import_only_into_empty_non_sqlite(tmp_path):
    src = tmp_path / "cutnkeep.db"
    _old_sqlite(src)
    settings = Settings.model_validate({"SERVICE_DB_IMPORT_FROM": str(src)})
    sqlite_target = create_engine(f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    Base.metadata.create_all(sqlite_target)
    assert auto_import(settings, sqlite_target) is None  # SQLite → SQLite 는 하지 않는다

    # 대상이 MariaDB 라고 치고(SQLite 건너뛰기 끔) 비어 있으면 한 번 옮긴다
    assert auto_import(settings, sqlite_target, skip_sqlite=False)["users"] == 1
    assert auto_import(settings, sqlite_target, skip_sqlite=False) is None  # 이미 회원이 있으면 건드리지 않는다
    with sqlite_target.connect() as conn:
        assert conn.execute(select(func.count()).select_from(Base.metadata.tables["users"])).scalar() == 1
    assert src.exists()  # 원본은 남긴다
