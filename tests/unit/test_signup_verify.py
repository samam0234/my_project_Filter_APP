# -*- coding: utf-8 -*-
"""회원가입 이메일 인증 — 신청(메일 발송) → 일련번호 입력 → 가입 완료.

앱 · 메모리 DB · 메일 가로채기는 tests/unit/conftest.py 의 api_env (기본은 인증 끔 → 여기서 켠다).
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
from app.models.user import SignupPending, User

GOOD_PW = "cutkeep2026"
SERIAL_RE = re.compile(r"\b([A-Z2-9]{4}-[A-Z2-9]{4})\b")


@pytest.fixture()
def env(api_env, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "signup_email_verification", True)
    monkeypatch.setattr(s, "cors_origins", "https://site.test")
    monkeypatch.setattr(s, "auth_code_resend_seconds", 0)  # 재발송 간격은 따로 검사한다
    return api_env


def _start(client, username="newbie_01", email="newbie@example.com", password=GOOD_PW, agree=True, **extra):
    return client.post(
        "/api/v1/auth/signup/start",
        json={"username": username, "email": email, "password": password, "agree_terms": agree, **extra},
    )


def _serial(env) -> str:
    return SERIAL_RE.search(env["mails"][-1]["body"]).group(1)


def _verify(client, email, code):
    return client.post("/api/v1/auth/signup/verify", json={"email": email, "code": code})


def _users(env) -> int:
    with env["Session"]() as db:
        return db.query(User).count()


# ------------------------------------------------------------------ 일련번호


def test_serial_format_and_normalizing():
    serial = pw.new_serial()
    assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{4}", serial)
    assert not set(serial) & set("01OIL")  # 헷갈리는 글자 없음
    assert pw.normalize_serial(" ab-cd 23x4 ") == "ABCD23X4"
    assert len({pw.new_serial() for _ in range(50)}) == 50


# ------------------------------------------------------------------ 신청 → 인증


def test_start_sends_mail_but_creates_no_user(env):
    c = env["client"]
    r = _start(c, display_name="새내기")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["verification_required"] is True and body["email"] == "newbie@example.com" and body["user"] is None
    assert _users(env) == 0
    assert "cnk_session" not in c.cookies  # 아직 로그인 상태가 아니다

    mail = env["mails"][-1]
    assert mail["to"] == "newbie@example.com" and "회원가입" in mail["subject"]
    assert SERIAL_RE.search(mail["body"]) and SERIAL_RE.search(mail["html"])
    assert "회원가입 인증" in mail["html"]
    assert 'href="https://site.test/signup/verify?email=newbie%40example.com"' in mail["html"]


def test_verify_with_the_mailed_serial_creates_account_and_logs_in(env):
    c = env["client"]
    _start(c, display_name="새내기")
    r = _verify(c, "newbie@example.com", _serial(env))
    assert r.status_code == 201, r.text
    assert r.json()["username"] == "newbie_01" and r.json()["display_name"] == "새내기"
    assert c.get("/api/v1/auth/me").status_code == 200  # 쿠키로 로그인 상태
    with env["Session"]() as db:
        user = db.query(User).one()
        assert user.terms_agreed_at is not None and pw.verify_password(GOOD_PW, user.password_hash)
        assert db.query(SignupPending).count() == 0  # 대기 건은 지워진다
    # 가입한 비밀번호로 다시 로그인도 된다
    c.post("/api/v1/auth/logout")
    assert c.post("/api/v1/auth/login", json={"username": "newbie_01", "password": GOOD_PW}).status_code == 200


def test_serial_is_case_space_and_hyphen_insensitive(env):
    c = env["client"]
    _start(c)
    typed = _serial(env).lower().replace("-", " ")
    assert _verify(c, "NewBie@Example.com", f" {typed} ").status_code == 201


def test_wrong_serial_counts_attempts_then_locks(env):
    c = env["client"]
    _start(c)
    good = _serial(env)
    for left in (4, 3, 2, 1):
        r = _verify(c, "newbie@example.com", "AAAA-BBBB")
        assert r.status_code == 400 and f"{left}번" in r.json()["detail"]
    r = _verify(c, "newbie@example.com", "AAAA-BBBB")  # 5번째 — 잠김
    assert r.status_code == 400 and "새로" in r.json()["detail"]
    assert _verify(c, "newbie@example.com", good).status_code == 400  # 맞는 번호도 이제 안 된다
    assert _users(env) == 0


def test_expired_serial_is_rejected(env):
    c = env["client"]
    _start(c)
    good = _serial(env)
    with env["Session"]() as db:
        p = db.query(SignupPending).one()
        p.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    r = _verify(c, "newbie@example.com", good)
    assert r.status_code == 400 and "만료" in r.json()["detail"]
    assert _users(env) == 0


def test_verify_without_start_or_for_another_email_fails(env):
    c = env["client"]
    assert _verify(c, "nobody@example.com", "AAAA-BBBB").status_code == 400
    _start(c)
    assert _verify(c, "other@example.com", _serial(env)).status_code == 400  # 남의 이메일로 번호만 맞춰도 안 된다


# ------------------------------------------------------------------ 입력 검사 · 중복


def test_start_validates_input_before_sending_mail(env):
    c = env["client"]
    assert _start(c, agree=False).status_code == 400
    assert _start(c, username="ab").status_code == 400
    assert _start(c, email="not-an-email").status_code == 400
    assert _start(c, password="short1").status_code == 400
    assert env["mails"] == []


def test_start_rejects_taken_username_and_email(env):
    c = env["client"]
    _start(c)
    _verify(c, "newbie@example.com", _serial(env))
    c.post("/api/v1/auth/logout")
    mails = len(env["mails"])
    assert _start(c, username="newbie_01", email="x@example.com").status_code == 409
    assert _start(c, username="someone_2", email="newbie@example.com").status_code == 409
    assert len(env["mails"]) == mails


def test_taken_in_the_meantime_is_caught_at_verify(env):
    c = env["client"]
    _start(c)
    good = _serial(env)
    with env["Session"]() as db:  # 신청 후 같은 아이디로 먼저 가입한 사람
        db.add(User(id="x" * 32, username="newbie_01", email="early@example.com", password_hash="h"))
        db.commit()
    r = _verify(c, "newbie@example.com", good)
    assert r.status_code == 409
    assert _users(env) == 1


def test_restarting_replaces_the_previous_pending_and_old_serial_dies(env):
    c = env["client"]
    _start(c)
    first = _serial(env)
    _start(c, username="newbie_02")  # 같은 이메일로 다시 신청 (아이디를 고침)
    second = _serial(env)
    with env["Session"]() as db:
        assert db.query(SignupPending).count() == 1
    assert first != second
    assert _verify(c, "newbie@example.com", first).status_code == 400
    assert _verify(c, "newbie@example.com", second).json()["username"] == "newbie_02"


# ------------------------------------------------------------------ 다시 받기 · 간격


def test_resend_issues_a_new_serial_and_resets_attempts(env):
    c = env["client"]
    _start(c)
    old = _serial(env)
    _verify(c, "newbie@example.com", "AAAA-BBBB")
    r = c.post("/api/v1/auth/signup/resend", json={"email": "newbie@example.com"})
    assert r.status_code == 200 and len(env["mails"]) == 2
    new = _serial(env)
    assert new != old
    with env["Session"]() as db:
        assert db.query(SignupPending).one().attempts == 0
    assert _verify(c, "newbie@example.com", old).status_code == 400
    assert _verify(c, "newbie@example.com", new).status_code == 201


def test_resend_respects_the_interval_and_needs_a_pending_signup(env, monkeypatch):
    c = env["client"]
    assert c.post("/api/v1/auth/signup/resend", json={"email": "nobody@example.com"}).status_code == 404
    monkeypatch.setattr(get_settings(), "auth_code_resend_seconds", 60)
    _start(c)
    r = c.post("/api/v1/auth/signup/resend", json={"email": "newbie@example.com"})
    assert r.status_code == 429 and "초 뒤" in r.json()["detail"]
    assert _start(c).status_code == 429  # 같은 이메일로 연타해도 메일을 쏟아내지 않는다
    assert len(env["mails"]) == 1


def test_mail_failure_does_not_leave_a_pending_signup(env, monkeypatch):
    from app.services import auth_service

    monkeypatch.setattr(auth_service, "send_mail", lambda *a, **k: False)
    r = _start(env["client"])
    assert r.status_code == 503 and "보내지 못했어요" in r.json()["detail"]
    with env["Session"]() as db:
        assert db.query(SignupPending).count() == 0


# ------------------------------------------------------------------ 인증 켬/끔


def test_direct_signup_is_closed_while_verification_is_on(env):
    r = env["client"].post(
        "/api/v1/auth/signup",
        json={"username": "bypass_01", "email": "b@example.com", "password": GOOD_PW, "agree_terms": True},
    )
    assert r.status_code == 403 and "이메일 인증" in r.json()["detail"]
    assert _users(env) == 0


def test_verification_off_signs_up_immediately(env, monkeypatch):
    monkeypatch.setattr(get_settings(), "signup_email_verification", False)
    c = env["client"]
    r = _start(c)
    assert r.status_code == 200 and r.json()["verification_required"] is False
    assert r.json()["user"]["username"] == "newbie_01"
    assert c.get("/api/v1/auth/me").status_code == 200 and env["mails"] == []


def test_maintenance_purges_only_expired_pending(env):
    from app.services import maintenance

    c = env["client"]
    _start(c, username="old_user", email="old@example.com")
    _start(c, username="new_user", email="new@example.com")
    with env["Session"]() as db:
        old = db.query(SignupPending).filter_by(email="old@example.com").one()
        old.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert maintenance.purge_signup_pending() == 1
    with env["Session"]() as db:
        assert [p.email for p in db.query(SignupPending).all()] == ["new@example.com"]
    assert maintenance.purge_signup_pending() == 0


def test_response_says_whether_mail_really_went_out(env, monkeypatch):
    """SMTP 미설정(개발 모드)이면 메일이 로그에만 남는다 — 화면이 사용자에게 알릴 수 있게 응답에 싣는다."""
    s = get_settings()
    monkeypatch.setattr(s, "smtp_host", "")
    c = env["client"]
    assert _start(c).json()["mail_delivered"] is False
    assert c.post("/api/v1/auth/signup/resend", json={"email": "newbie@example.com"}).json()["mail_delivered"] is False
    monkeypatch.setattr(s, "smtp_host", "smtp.test")
    assert _start(c, username="newbie_02", email="n2@example.com").json()["mail_delivered"] is True
