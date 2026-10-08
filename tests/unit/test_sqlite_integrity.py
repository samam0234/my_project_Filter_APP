# -*- coding: utf-8 -*-
"""서비스 DB 손상 감지 · 호스트/Docker 파일 분리 기본값.

2026-10-08 호스트 backend 와 Docker backend 가 같은 SQLite 파일을 번갈아 쓰다 jobs 루트 페이지가
다른 프로세스의 로그 텍스트로 덮여 업로드가 모두 500 이 됐다. 기동 시 quick_check 로 바로 드러나야 한다.
"""

from __future__ import annotations

import sqlite3

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine

from app.core.config import Settings
from app.db.session import check_sqlite_integrity


def _make_db(path):
    con = sqlite3.connect(path)
    con.execute("create table users (id text primary key, name text)")
    con.execute("create table jobs (id text primary key, prompt text)")
    con.executemany("insert into jobs values (?, ?)", [(str(i), "x" * 200) for i in range(200)])
    con.commit()
    con.close()


def test_quick_check_ok(tmp_path):
    db = tmp_path / "ok.db"
    _make_db(db)
    assert check_sqlite_integrity(create_engine(f"sqlite:///{db.as_posix()}")) == "ok"


def test_quick_check_detects_overwritten_page(tmp_path):
    db = tmp_path / "broken.db"
    _make_db(db)
    # 실제 사고처럼 테이블 페이지 하나를 로그 텍스트로 덮는다
    data = bytearray(db.read_bytes())
    page = 4096
    assert len(data) > 4 * page
    text = b"[ WARN:5@16.155] global cap.cpp:781 cv::VideoWriter::open VIDEOIO(CV_IMAGES)\r\n" * 50
    data[3 * page:4 * page] = text[:page]
    db.write_bytes(bytes(data))
    assert check_sqlite_integrity(create_engine(f"sqlite:///{db.as_posix()}")) != "ok"


def test_non_sqlite_is_skipped():
    class _Dialect:
        name = "mysql"

    class _Eng:
        dialect = _Dialect()

    assert check_sqlite_integrity(_Eng()) == "skip"  # type: ignore[arg-type]


def test_host_default_differs_from_docker_file():
    """호스트 기본 파일은 Docker(compose 의 data/cutnkeep.db)와 달라야 한다."""
    assert Settings.model_fields["sqlite_path"].default == "data/cutnkeep.host.db"
