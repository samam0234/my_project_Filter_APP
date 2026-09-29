"""메일 발송 (아이디 찾기 · 비밀번호 재설정 코드).

- SMTP_HOST 가 설정돼 있으면 smtplib 로 발송 (STARTTLS 선택)
- 비어 있으면 **개발 모드**: 보내지 않고 서버 로그(backend/logs)에 본문을 남긴다
- 발송 실패는 예외를 올리지 않고 로그만 남긴다 → API 는 항상 같은 안내를 돌려줘
  메일 성공 여부로 계정 존재를 추측할 수 없게 한다
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

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
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        logger.info("메일 발송 to={} subject={}", to, subject)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("메일 발송 실패 to={} subject={} err={}", to, subject, exc)
        return False
