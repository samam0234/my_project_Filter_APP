# -*- coding: utf-8 -*-
"""배포 설정 점검 · 보안 헤더 테스트."""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic_settings")
pytest.importorskip("loguru")

from app.core import preflight
from app.core.config import Settings

SAFE = {
    "APP_ENV": "production",
    "DEBUG": False,
    "SECRET_KEY": "x" * 48,
    "SESSION_COOKIE_SECURE": True,
    "SMTP_HOST": "smtp.example.com",
    "CORS_ORIGINS": "https://cutnkeep.example.com",
    "MARIADB_PASSWORD": "a-long-random-db-password",
    "LEARNING_DB_FALLBACK_SQLITE": False,
}


# 코드 기본값 (config.py) — .env 로 덮인 값을 테스트가 따라가지 않게 직접 넣는다
DEV_DEFAULTS = {"SECRET_KEY": "dev-secret-change-me", "DEBUG": True, "SESSION_COOKIE_SECURE": False, "SMTP_HOST": ""}


def _keys(settings, level="error"):
    return {i.key for i in preflight.check(settings) if i.level == level}


def test_development_defaults_are_reported_but_not_blocking():
    # 기본값 그대로를 명시 — 로컬 .env 에 이미 안전한 값(SECRET_KEY·DEBUG=false)을 넣어도 결과가 같게
    s = Settings.model_validate({"APP_ENV": "development", **DEV_DEFAULTS})
    assert {"SECRET_KEY", "DEBUG", "SESSION_COOKIE_SECURE", "SMTP_HOST"} <= _keys(s)
    assert preflight.blocking(s, preflight.check(s)) == []


def test_production_with_defaults_is_blocked():
    s = Settings.model_validate(  # .env · CI 환경변수와 무관하게
        {"APP_ENV": "production", "MARIADB_PASSWORD": "cutnkeep", "LEARNING_DB_DIALECT": "mariadb", **DEV_DEFAULTS}
    )
    blocked = {i.key for i in preflight.blocking(s, preflight.check(s))}
    assert {"SECRET_KEY", "DEBUG", "SESSION_COOKIE_SECURE", "SMTP_HOST", "MARIADB_PASSWORD"} <= blocked


def test_production_safe_settings_pass(monkeypatch):
    s = Settings.model_validate(SAFE)
    errors = _keys(s) - {"YOLO_MODEL_PATH"}  # 가중치 파일 유무는 실행 환경에 따름
    assert errors == set()
    assert "CORS_ORIGINS" not in _keys(s, "warn")


@pytest.mark.parametrize(
    "override,key",
    [
        ({"CORS_ORIGINS": "*"}, "CORS_ORIGINS"),
        ({"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""}, "OPENAI_API_KEY"),
        ({"SECRET_KEY": "short-but-custom"}, "SECRET_KEY"),
    ],
)
def test_specific_production_errors(override, key):
    assert key in _keys(Settings.model_validate({**SAFE, **override}))


def test_strict_can_be_disabled():
    s = Settings.model_validate({"APP_ENV": "production", "PREFLIGHT_STRICT": False})
    assert preflight.blocking(s, preflight.check(s)) == []


def test_security_headers(api_env):
    r = api_env["client"].get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in r.headers  # 로컬 http (SESSION_COOKIE_SECURE=false)
