#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMTP 설정 확인 — 지금 .env 의 SMTP_* 로 테스트 메일 한 통을 보낸다.

사용:
  python scripts/send_test_mail.py you@example.com
  docker exec cut_and_keep-backend-1 python /app/scripts/send_test_mail.py you@example.com   (이미지에 scripts 가 있을 때)

SMTP_HOST 가 비어 있으면 실제로 보내지 않고 서버 로그에만 남는다(개발 모드) — 그 사실을 알려 준다.
성공하면 0, 실패하면 1 로 끝난다. 실패 원인(인증 · TLS · 포트)은 backend 로그의 "메일 발송 실패" 줄을 본다.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.services.mailer import send_mail  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2 or "@" not in sys.argv[1]:
        print("사용: python scripts/send_test_mail.py 받는주소@example.com")
        return 2
    to = sys.argv[1]
    s = get_settings()
    if not s.smtp_host:
        print("SMTP_HOST 가 비어 있다 — 개발 모드라 실제로 보내지 않고 서버 로그에만 남긴다.")
    mode = "SSL" if s.smtp_ssl else ("STARTTLS" if s.smtp_starttls else "평문")
    print(f"보내는 서버: {s.smtp_host or '(없음)'}:{s.smtp_port} · {mode} · 계정 {s.smtp_user or '(없음)'} · 보내는 사람 {s.smtp_from}")
    ok = send_mail(
        to,
        "[컷앤킵] 메일 설정 확인",
        f"컷앤킵 메일 설정이 동작합니다.\n보낸 시각: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
        "이 메일을 받았다면 아이디 찾기 · 비밀번호 재설정 코드도 같은 방식으로 발송됩니다.",
        s,
    )
    print("발송 성공" if ok else "발송 실패 — 로그의 '메일 발송 실패' 줄을 확인하세요 (계정 · 앱 비밀번호 · 포트 · SSL/STARTTLS)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
