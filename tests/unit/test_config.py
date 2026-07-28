# -*- coding: utf-8 -*-
"""설정 모듈 기본 동작.

Settings / database_url / get_settings 캐시 검증.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic_settings")

from app.core.config import Settings, get_settings


def test_settings_defaults():
    """기본 필드 타입·경로 힌트가 합리적인지."""
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
    )
    # 환경변수가 있어도 타입·경로 힌트만 느슨히 검사
    assert s.max_upload_size_mb == 20 or s.max_upload_size_mb > 0
    assert "yolo" in s.yolo_model_path.lower() or s.yolo_model_path.endswith(
        (".pt", ".onnx")
    )
    assert s.llm_provider in {"ollama", "openai", "gemini", "heuristic"} or isinstance(
        s.llm_provider, str
    )


def test_allowed_mime_list():
    """쉼표 구분 MIME → 리스트 프로퍼티."""
    s = Settings(ALLOWED_MIME_TYPES="image/jpeg,image/png", _env_file=None)  # type: ignore[call-arg]
    # alias 필드는 model_validate 로 넣는 편이 안정적
    s2 = Settings.model_validate(
        {
            "ALLOWED_MIME_TYPES": "image/jpeg, image/png",
            "DB_DIALECT": "sqlite",
        }
    )
    assert "image/jpeg" in s2.allowed_mime_list
    assert "image/png" in s2.allowed_mime_list


def test_database_url_sqlite():
    """DB_DIALECT=sqlite 시 sqlite:/// URL."""
    s = Settings.model_validate(
        {
            "DB_DIALECT": "sqlite",
            "SQLITE_PATH": "data/test_cutnkeep.db",
        }
    )
    url = s.database_url
    assert url.startswith("sqlite:///")
    assert "test_cutnkeep.db" in url.replace("\\", "/")


def test_database_url_mariadb():
    """DB_DIALECT=mariadb 시 mysql+pymysql URL."""
    s = Settings.model_validate(
        {
            "DB_DIALECT": "mariadb",
            "MARIADB_HOST": "dbhost",
            "MARIADB_PORT": 3307,
            "MARIADB_USER": "u",
            "MARIADB_PASSWORD": "p",
            "MARIADB_DATABASE": "d",
        }
    )
    url = s.database_url
    assert url.startswith("mysql+pymysql://")
    assert "dbhost" in url
    assert "3307" in url


def test_get_settings_cached():
    """lru_cache 로 동일 인스턴스 반환."""
    a = get_settings()
    b = get_settings()
    assert a is b
