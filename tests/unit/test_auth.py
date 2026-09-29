# -*- coding: utf-8 -*-
"""계정 API 테스트 — 회원가입 · 로그인/잠금 · 세션 · 아이디 찾기 · 비밀번호 재설정.

앱·메모리 DB·메일 가로채기는 tests/unit/conftest.py 의 api_env fixture.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from app.core import passwords as pw
from app.core.config import get_settings
from app.models.user import AuthCode, User

GOOD_PW = "cutkeep2026"


@pytest.fixture()
def env(api_env):
    return api_env


def _signup(client, username="tester_01", email="tester@example.com", password=GOOD_PW, name="테스터"):
    return client.post(
        "/api/v1/auth/signup",
        json={"username": username, "email": email, "password": password, "display_name": name},
    )


# ------------------------------------------------------------------ 비밀번호 유틸


def test_password_hash_roundtrip():
    h = pw.hash_password("secret123")
    assert h.startswith("scrypt$") and "secret123" not in h
    assert pw.verify_password("secret123", h)
    assert not pw.verify_password("secret124", h)
    assert pw.hash_password("secret123") != h  # salt


@pytest.mark.parametrize("bad", ["short1", "onlyletters", "12345678", "a" * 70 + "1"])
def test_password_rules(bad):
    assert pw.password_problem(bad) is not None


# ------------------------------------------------------------------ 회원가입


def test_signup_sets_http_only_cookie_and_me(env):
    c = env["client"]
    r = _signup(c)
    assert r.status_code == 201, r.text
    assert r.json()["username"] == "tester_01"
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    me = c.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["email"] == "tester@example.com"


def test_signup_normalizes_case_and_rejects_duplicates(env):
    c = env["client"]
    assert _signup(c, username="Tester_01", email="Tester@Example.com").status_code == 201
    assert _signup(c, username="tester_01", email="other@example.com").status_code == 409
    assert _signup(c, username="another_1", email="TESTER@example.com").status_code == 409


@pytest.mark.parametrize(
    "field,value,fragment",
    [
        ("username", "ab", "아이디"),
        ("username", "한글아이디", "아이디"),
        ("email", "not-an-email", "이메일"),
        ("password", "abcdefgh", "영문과 숫자"),
    ],
)
def test_signup_validation_messages(env, field, value, fragment):
    kwargs = {"username": "valid_user", "email": "v@example.com", "password": GOOD_PW}
    kwargs[field] = value
    r = _signup(env["client"], **kwargs)
    assert r.status_code == 400 and fragment in r.json()["detail"]


def test_password_is_not_stored_plain(env):
    _signup(env["client"])
    with env["Session"]() as db:
        user = db.query(User).one()
        assert GOOD_PW not in user.password_hash


# ------------------------------------------------------------------ 로그인 · 세션


def test_login_logout_flow(env):
    c = env["client"]
    _signup(c)
    c.cookies.clear()
    assert c.get("/api/v1/auth/me").status_code == 401

    r = c.post("/api/v1/auth/login", json={"username": "TESTER_01", "password": GOOD_PW})
    assert r.status_code == 200
    assert c.get("/api/v1/auth/me").status_code == 200

    token = c.cookies.get(get_settings().session_cookie_name)
    assert c.post("/api/v1/auth/logout").status_code == 200
    # 서버 측 세션이 폐기돼 같은 토큰을 다시 보내도 401
    c.cookies.set(get_settings().session_cookie_name, token)
    assert c.get("/api/v1/auth/me").status_code == 401


def test_login_errors_do_not_reveal_which_part_is_wrong(env):
    c = env["client"]
    _signup(c)
    wrong_pw = c.post("/api/v1/auth/login", json={"username": "tester_01", "password": "nope12345"})
    no_user = c.post("/api/v1/auth/login", json={"username": "ghost_user", "password": "nope12345"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]


def test_login_locks_after_repeated_failures(env):
    c = env["client"]
    _signup(c)
    limit = get_settings().login_max_failures
    for _ in range(limit):
        c.post("/api/v1/auth/login", json={"username": "tester_01", "password": "wrong1234"})
    locked = c.post("/api/v1/auth/login", json={"username": "tester_01", "password": GOOD_PW})
    assert locked.status_code == 429


def test_expired_session_is_rejected(env):
    c = env["client"]
    _signup(c)
    with env["Session"]() as db:
        from app.models.user import AuthSession

        for s in db.query(AuthSession).all():
            s.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert c.get("/api/v1/auth/me").status_code == 401


# ------------------------------------------------------------------ 아이디 찾기


def test_find_id_mails_username_and_response_is_generic(env):
    c = env["client"]
    _signup(c)
    known = c.post("/api/v1/auth/find-id", json={"email": "TESTER@example.com"})
    unknown = c.post("/api/v1/auth/find-id", json={"email": "nobody@example.com"})
    assert known.json()["message"] == unknown.json()["message"]
    assert len(env["mails"]) == 1
    assert env["mails"][0]["to"] == "tester@example.com"
    assert "tester_01" in env["mails"][0]["body"]
    assert "tester_01" not in known.text  # 화면(응답)에는 아이디를 노출하지 않음


# ------------------------------------------------------------------ 비밀번호 재설정


def _request_code(env, username="tester_01", email="tester@example.com") -> str:
    env["client"].post("/api/v1/auth/password/request", json={"username": username, "email": email})
    body = env["mails"][-1]["body"]
    return re.search(r"(\d{6})", body).group(1)


def test_password_reset_flow_revokes_sessions(env):
    c = env["client"]
    _signup(c)
    assert c.get("/api/v1/auth/me").status_code == 200
    code = _request_code(env)

    r = c.post(
        "/api/v1/auth/password/reset",
        json={"username": "tester_01", "code": code, "new_password": "newpass2026"},
    )
    assert r.status_code == 200, r.text
    assert c.get("/api/v1/auth/me").status_code == 401  # 모든 세션 로그아웃
    assert c.post("/api/v1/auth/login", json={"username": "tester_01", "password": GOOD_PW}).status_code == 401
    assert c.post("/api/v1/auth/login", json={"username": "tester_01", "password": "newpass2026"}).status_code == 200
    # 같은 코드 재사용 불가
    again = c.post(
        "/api/v1/auth/password/reset",
        json={"username": "tester_01", "code": code, "new_password": "another2026"},
    )
    assert again.status_code == 400


def test_password_request_is_generic_and_mismatch_sends_nothing(env):
    c = env["client"]
    _signup(c)
    ok = c.post("/api/v1/auth/password/request", json={"username": "tester_01", "email": "wrong@example.com"})
    ghost = c.post("/api/v1/auth/password/request", json={"username": "ghost_user", "email": "x@example.com"})
    assert ok.json()["message"] == ghost.json()["message"]
    assert env["mails"] == []


def test_code_is_invalidated_after_max_attempts(env):
    c = env["client"]
    _signup(c)
    code = _request_code(env)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(get_settings().auth_code_max_attempts):
        c.post("/api/v1/auth/password/reset", json={"username": "tester_01", "code": wrong, "new_password": "newpass2026"})
    r = c.post("/api/v1/auth/password/reset", json={"username": "tester_01", "code": code, "new_password": "newpass2026"})
    assert r.status_code == 400


def test_expired_code_rejected_and_resend_throttled(env):
    c = env["client"]
    _signup(c)
    code = _request_code(env)
    _request_code(env)  # 재발송 간격 이내 → 새 메일 없음
    assert len(env["mails"]) == 1
    with env["Session"]() as db:
        for rec in db.query(AuthCode).all():
            rec.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    r = c.post("/api/v1/auth/password/reset", json={"username": "tester_01", "code": code, "new_password": "newpass2026"})
    assert r.status_code == 400


# ------------------------------------------------------------------ 작업 연결


def test_mine_filter_requires_login(env):
    c = env["client"]
    assert c.get("/api/v1/jobs?mine=true").status_code == 401
    _signup(c)
    r = c.get("/api/v1/jobs?mine=true")
    assert r.status_code == 200 and r.json() == []
