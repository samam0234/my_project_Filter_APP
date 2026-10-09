#!/usr/bin/env python3
"""운영 서버용 .env 만들기 — .env.example 을 바탕으로 운영 값을 채우고, 바로 기동 전 점검(preflight)을 돌린다.

손으로 .env 를 고치다 빠뜨리기 쉬운 것(APP_ENV · DEBUG · 쿠키 Secure · CORS · 콘솔 로그인 · 학습 DB 폴백 · 기본 DB 비밀번호)을
한 번에 맞추고, 비밀 값(SECRET_KEY · MariaDB 비밀번호)은 새 난수로 만든다.

비밀번호는 명령줄에 쓰지 않는다 (셸 기록 · 프로세스 목록에 남는다) — 환경 변수로 넘긴다:
  CNK_SMTP_PASSWORD   메일 발송 계정 비밀번호 (없으면 빈칸 — 나중에 .env 에서 채운다)

실행 (서버의 저장소 폴더):
  python scripts/make_prod_env.py --domain cutnkeep.example.com --acme-email you@example.com \\
      --smtp-host smtp.gmail.com --smtp-port 587 --smtp-user you@gmail.com --smtp-from "Cut & Keep <you@gmail.com>" \\
      --operator-name 홍길동 --operator-email privacy@example.com --console-admins admin
  → .env.production (git 제외). 확인 후 서버에서 .env 로 이름을 바꾸거나 --env-file .env.production 으로 compose 를 띄운다
  python scripts/make_prod_env.py --check .env.production      # 이미 있는 파일만 점검

주의: MariaDB 비밀번호는 DB 를 처음 만들 때만 적용된다. 이미 데이터가 있는 서버에서 바꾸려면 DB 안에서 비밀번호를 바꾸거나
      (ALTER USER) 백업 → 볼륨 재생성 → 복구 (docs/DATABASE.md). 새 서버라면 그대로 쓰면 된다.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _set(lines: list[str], key: str, value: str) -> list[str]:
    """KEY= 줄을 바꾼다. 주석 처리된 예시(# KEY=)만 있으면 그 자리에 실제 줄을 넣고, 없으면 끝에 붙인다."""
    pat = re.compile(rf"^\s*{re.escape(key)}=")
    commented = re.compile(rf"^\s*#\s*{re.escape(key)}=")
    for i, line in enumerate(lines):
        if pat.match(line):
            lines[i] = f"{key}={value}"
            return lines
    for i, line in enumerate(lines):
        if commented.match(line):
            lines.insert(i + 1, f"{key}={value}")
            return lines
    lines.append(f"{key}={value}")
    return lines


def build(args) -> str:
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    https = f"https://{args.domain}"
    values = {
        "APP_ENV": "production",
        "DEBUG": "false",
        "SECRET_KEY": secrets.token_urlsafe(48),
        "SESSION_COOKIE_SECURE": "true",
        "DOMAIN": args.domain,
        "ACME_EMAIL": args.acme_email,
        "CORS_ORIGINS": https,
        "SMTP_HOST": args.smtp_host,
        "SMTP_PORT": str(args.smtp_port),
        "SMTP_USER": args.smtp_user,
        "SMTP_PASSWORD": os.environ.get("CNK_SMTP_PASSWORD", ""),
        "SMTP_FROM": args.smtp_from or f"Cut & Keep <{args.smtp_user}>",
        "SMTP_STARTTLS": "false" if args.smtp_port == 465 else "true",
        "SMTP_SSL": "true" if args.smtp_port == 465 else "false",
        "OPERATOR_NAME": args.operator_name,
        "OPERATOR_EMAIL": args.operator_email,
        "POLICY_DATE": args.policy_date or date.today().isoformat(),
        "CONSOLE_ADMINS": args.console_admins,
        "CONSOLE_REQUIRE_LOGIN": "true",
        "CONSOLE_ALLOW_REMOTE": "false",
        "LEARNING_DB_FALLBACK_SQLITE": "false",
        "MARIADB_PASSWORD": secrets.token_urlsafe(24),
        "MYSQL_ROOT_PASSWORD": secrets.token_urlsafe(24),
    }
    for k, v in values.items():
        lines = _set(lines, k, v)
    head = [
        f"# 운영 .env — scripts/make_prod_env.py 가 {date.today().isoformat()} 에 만듦 (git 에 올리지 않는다)",
        "# 비밀 값(SECRET_KEY · MARIADB_PASSWORD · MYSQL_ROOT_PASSWORD · SMTP_PASSWORD)은 이 파일에만 있다 — 서버 밖으로 복사하지 않는다",
        "",
    ]
    return "\n".join(head + lines) + "\n"


def check(path: Path) -> int:
    """기동 전 점검(preflight)을 이 파일 값으로 돌린다 — 백엔드가 production 에서 기동을 거부할 항목(error)이 있으면 1."""
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.config import Settings
    from app.core.preflight import check as preflight

    settings = Settings(_env_file=str(path))
    issues = preflight(settings)
    errors = [i for i in issues if i.level == "error"]
    print(f"[preflight] {path.name}: APP_ENV={settings.app_env} · 오류 {len(errors)} · 경고 {len(issues) - len(errors)}")
    for i in issues:
        print(f"  {'✗' if i.level == 'error' else '!'} {i.key}: {i.message}")
    if not settings.smtp_password:
        print("  ! SMTP_PASSWORD 가 비어 있다 — 메일 발송 계정이 비밀번호를 요구하면 채운다 (CNK_SMTP_PASSWORD 로 다시 만들거나 파일에서)")
    if not errors:
        print("  ✓ 기동 거부 항목 없음 — 띄운 뒤 python scripts/deploy_check.py remote https://<도메인> · server 로 점검")
    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="운영 .env 만들기 · 점검")
    ap.add_argument("--check", type=Path, help="이미 있는 env 파일만 점검")
    ap.add_argument("--out", type=Path, default=ROOT / ".env.production")
    ap.add_argument("--force", action="store_true", help="있는 파일을 덮어쓴다 (비밀 값이 바뀐다)")
    ap.add_argument("--domain")
    ap.add_argument("--acme-email")
    ap.add_argument("--smtp-host")
    ap.add_argument("--smtp-port", type=int, default=587)
    ap.add_argument("--smtp-user", default="")
    ap.add_argument("--smtp-from", default="")
    ap.add_argument("--operator-name", default="")
    ap.add_argument("--operator-email", default="")
    ap.add_argument("--policy-date", default="")
    ap.add_argument("--console-admins", default="", help="운영 콘솔에 들어갈 회원 아이디 (쉼표)")
    args = ap.parse_args()
    if args.check:
        return check(args.check)
    missing = [k for k in ("domain", "acme_email", "smtp_host") if not getattr(args, k)]
    if missing:
        ap.error("필수: " + ", ".join("--" + k.replace("_", "-") for k in missing))
    if args.out.exists() and not args.force:
        print(f"{args.out} 가 이미 있다 — 덮어쓰면 SECRET_KEY · DB 비밀번호가 바뀐다 (--force)")
        return 1
    args.out.write_text(build(args), encoding="utf-8")
    try:
        os.chmod(args.out, 0o600)  # 리눅스 서버: 소유자만 읽기
    except OSError:
        pass
    print(f"만듦: {args.out}")
    return check(args.out)


if __name__ == "__main__":
    sys.exit(main())
