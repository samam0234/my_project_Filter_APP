"""메일 발송 (아이디 찾기 · 비밀번호 재설정 코드).

- SMTP_HOST 가 설정돼 있으면 smtplib 로 발송
  · 포트 587 등: 평문 연결 후 STARTTLS (`SMTP_STARTTLS=true`)
  · 포트 465: 처음부터 TLS (`SMTP_SSL=true`) — 네이버 · 다음 · Gmail 등에서 흔함
  · 개발용 Mailpit(compose 프로필 mail): SMTP_HOST=mailpit, SMTP_PORT=1025, STARTTLS·SSL 끔
- 비어 있으면 **개발 모드**: 보내지 않고 서버 로그(backend/logs)에 본문을 남긴다
- 발송 실패는 예외를 올리지 않고 로그만 남긴다 → API 는 항상 같은 안내를 돌려줘
  메일 성공 여부로 계정 존재를 추측할 수 없게 한다
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from loguru import logger

from app.core.config import Settings, get_settings


def send_mail(to: str, subject: str, body: str, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not settings.smtp_host:
        logger.warning("[DEV MAIL · SMTP 미설정] to={} subject={}\n{}", to, subject, body)
        return True

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    # Date · Message-ID 가 없으면 받는 쪽이 스팸으로 분류하기 쉽다
    msg["Date"] = formatdate(localtime=True)
    domain = parseaddr(settings.smtp_from)[1].partition("@")[2] or "cutnkeep.local"
    msg["Message-ID"] = make_msgid(domain=domain)
    msg.set_content(body)
    try:
        context = ssl.create_default_context()
        if settings.smtp_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15, context=context)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
        with server as smtp:
            if settings.smtp_starttls and not settings.smtp_ssl:
                smtp.starttls(context=context)
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        logger.info("메일 발송 to={} subject={}", to, subject)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("메일 발송 실패 to={} subject={} err={}", to, subject, exc)
        return False
