# -*- coding: utf-8 -*-
"""메일 본문 템플릿 · HTML 발송 · 메일 속 버튼 주소(site_url)."""

from __future__ import annotations

import re
from email import message_from_bytes, policy

import pytest

from app.core.config import Settings
from app.services import mail_templates as mt
from app.services import mailer


def test_templates_have_text_and_html_with_the_same_facts():
    m = mt.password_reset(code="123456", reset_url="https://x.test/find-password", ttl_minutes=10, name="홍길동")
    assert m.subject.startswith("[컷앤킵]")
    for body in (m.text, m.html):
        assert "123456" in body and "https://x.test/find-password" in body and "10분" in body
    assert "<table" in m.html and 'lang="ko"' in m.html and "홍길동" in m.html
    assert "<" not in m.text  # 대체 본문에는 태그가 섞이지 않는다


def test_find_id_template_shows_username_and_login_button():
    m = mt.find_id(username="member_01", login_url="https://x.test/login")
    assert "member_01" in m.html and "member_01" in m.text
    assert re.search(r'<a href="https://x.test/login"[^>]*>로그인하기</a>', m.html)


def test_signup_template_has_serial_and_verify_button():
    m = mt.signup_verify(code="ABCD-2345", verify_url="https://x.test/signup/verify?email=a%40b.c", ttl_minutes=30)
    assert "ABCD-2345" in m.html and "ABCD-2345" in m.text
    assert "회원가입 인증" in m.html
    assert 'href="https://x.test/signup/verify?email=a%40b.c"' in m.html


def test_user_supplied_values_are_escaped():
    m = mt.find_id(username="<b>x</b>", login_url='https://x.test/"onmouseover="a', name="<script>alert(1)</script>")
    assert "<script>" not in m.html and "&lt;script&gt;" in m.html
    assert "<b>x</b>" not in m.html
    assert '"onmouseover="a' not in m.html  # 따옴표 이스케이프로 속성 탈출 불가


def test_send_mail_builds_multipart_alternative(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, *a, **k): ...
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **k): ...
        def login(self, *a): ...
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    s = Settings(SMTP_HOST="smtp.test", SMTP_USER="u", SMTP_PASSWORD="p", SMTP_FROM="Cut & Keep <a@b.c>")
    assert mailer.send_mail("to@x.test", "제목", "텍스트 본문", s, html="<p>HTML 본문</p>")
    msg = message_from_bytes(sent[0].as_bytes(), policy=policy.default)
    types = [part.get_content_type() for part in msg.walk()]
    assert types[0] == "multipart/alternative" and "text/plain" in types and "text/html" in types
    assert "텍스트 본문" in msg.get_body(("plain",)).get_content()
    assert "HTML 본문" in msg.get_body(("html",)).get_content()


def test_send_mail_without_html_stays_plain(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, *a, **k): ...
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **k): ...
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    mailer.send_mail("to@x.test", "제목", "본문", Settings(SMTP_HOST="smtp.test"))
    assert sent[0].get_content_type() == "text/plain"


# ------------------------------------------------------------------ 메일 속 주소 · 발송 연결

GOOD_PW = "cutkeep2026"


@pytest.fixture()
def env(api_env, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "cors_origins", "https://main.test,https://front.test")
    return api_env


def _signup(client):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "mailer_01", "email": "m@example.com", "password": GOOD_PW, "agree_terms": True},
    )


def test_find_id_mail_is_html_and_links_to_the_origin_the_user_came_from(env):
    c = env["client"]
    _signup(c)
    c.post("/api/v1/auth/find-id", json={"email": "m@example.com"}, headers={"Origin": "https://front.test"})
    mail = env["mails"][-1]
    assert mail["html"] and "mailer_01" in mail["html"]
    assert 'href="https://front.test/login"' in mail["html"]


def test_unknown_origin_falls_back_to_first_allowed_origin(env):
    c = env["client"]
    _signup(c)
    c.post("/api/v1/auth/find-id", json={"email": "m@example.com"}, headers={"Origin": "https://evil.test"})
    html = env["mails"][-1]["html"]
    assert "evil.test" not in html and 'href="https://main.test/login"' in html


def test_reset_mail_has_code_and_reset_link(env):
    c = env["client"]
    _signup(c)
    c.post(
        "/api/v1/auth/password/request",
        json={"username": "mailer_01", "email": "m@example.com"},
        headers={"Origin": "https://front.test"},
    )
    mail = env["mails"][-1]
    code = re.search(r"(\d{6})", mail["body"]).group(1)
    assert code in mail["html"] and 'href="https://front.test/find-password"' in mail["html"]
