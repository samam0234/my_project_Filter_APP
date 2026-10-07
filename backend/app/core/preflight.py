"""배포 전 설정 점검 — APP_ENV=production 에서 위험한 기본값으로 뜨지 않게.

기동(lifespan) 때 자동으로 돌고, 배포 전에 직접 돌릴 수도 있다:
  cd backend && python -m app.core.preflight          # 현재 .env 기준
  cd backend && APP_ENV=production python -m app.core.preflight

level
  error : production 이면 기동 거부 (PREFLIGHT_STRICT=false 로 경고만)
  warn  : 로그만
development 에서는 모두 경고로만 남긴다 (로컬 개발 기본값은 정상).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from app.core.config import Settings, get_settings

DEFAULT_SECRETS = {"dev-secret-change-me", "change-me-in-production", "secret", "changeme", ""}
DEFAULT_DB_PASSWORDS = {"cutnkeep", "change-me-db-password", "password", "admin", ""}
MIN_SECRET_LEN = 32


@dataclass(frozen=True)
class Issue:
    level: str  # error | warn
    key: str
    message: str


def check(settings: Settings) -> list[Issue]:
    issues: list[Issue] = []

    def add(level: str, key: str, message: str) -> None:
        issues.append(Issue(level, key, message))

    if settings.secret_key in DEFAULT_SECRETS or len(settings.secret_key) < MIN_SECRET_LEN:
        add("error", "SECRET_KEY",
            f"기본값이거나 {MIN_SECRET_LEN}자 미만 — 재설정 코드 HMAC 키. "
            "python -c \"import secrets; print(secrets.token_urlsafe(48))\" 로 생성")
    if settings.debug:
        add("error", "DEBUG", "true — 배포에서는 false")
    if not settings.session_cookie_secure:
        add("error", "SESSION_COOKIE_SECURE", "false — HTTPS 배포에서는 true (세션 쿠키가 평문 전송될 수 있음)")
    if not settings.smtp_host:
        add("error", "SMTP_HOST", "비어 있음 — 아이디 찾기·비밀번호 재설정 코드가 메일 대신 서버 로그에 남는다")
    origins = settings.cors_origin_list
    if "*" in origins:
        add("error", "CORS_ORIGINS", "'*' 는 쿠키 인증과 함께 쓸 수 없다 — 실제 도메인을 나열")
    elif origins and all("localhost" in o or "127.0.0.1" in o for o in origins):
        add("warn", "CORS_ORIGINS", "localhost 만 있음 — 배포 프론트 도메인(예: Vercel·Cloudflare) 추가")
    uses_maria = (settings.db_dialect or "").lower() in {"mariadb", "mysql"} or (
        settings.learning_db_dialect or ""
    ).lower() in {"mariadb", "mysql"}
    if uses_maria and settings.mariadb_password in DEFAULT_DB_PASSWORDS:
        add("error", "MARIADB_PASSWORD", "기본 비밀번호 — 교체 후 DB 볼륨 재생성")
    if settings.console_allow_remote:
        add("warn", "CONSOLE_ALLOW_REMOTE",
            "true — 누구나 콘솔 API 를 쓴다. 관리자 로그인(CONSOLE_ADMINS)으로 바꾸고 false 권장")
    if not settings.console_require_login:
        add("warn", "CONSOLE_REQUIRE_LOGIN",
            "false — 같은 서버의 리버스 프록시를 거치면 모든 요청이 127.0.0.1 로 보여 콘솔이 열릴 수 있다. 배포에서는 true")
    if settings.console_require_login and not settings.console_admin_set:
        add("warn", "CONSOLE_ADMINS", "비어 있음 — CONSOLE_REQUIRE_LOGIN=true 라 아무도 운영 콘솔에 들어갈 수 없다")
    if settings.learning_db_fallback_sqlite and uses_maria:
        add("warn", "LEARNING_DB_FALLBACK_SQLITE",
            "true — MariaDB 장애 시 조용히 로컬 SQLite 로 바뀐다. 배포에서는 false 권장 (/health learning_db 감시)")
    provider = (settings.llm_provider or "").lower()
    if provider == "openai" and not settings.openai_api_key:
        add("error", "OPENAI_API_KEY", "LLM_PROVIDER=openai 인데 키가 없다 — 모든 요청이 키워드 파서로 떨어짐")
    if provider == "gemini" and not settings.gemini_api_key:
        add("error", "GEMINI_API_KEY", "LLM_PROVIDER=gemini 인데 키가 없다 — 모든 요청이 키워드 파서로 떨어짐")
    if not settings.yolo_model_file.is_file():
        add("error", "YOLO_MODEL_PATH", f"세그 가중치 없음 ({settings.yolo_model_file}) — stub 마스크로 동작")
    return issues


def is_production(settings: Settings) -> bool:
    return (settings.app_env or "").strip().lower() in {"production", "prod"}


def blocking(settings: Settings, issues: list[Issue]) -> list[Issue]:
    """기동을 막을 항목 (production + strict 일 때 error)."""
    if not (is_production(settings) and settings.preflight_strict):
        return []
    return [i for i in issues if i.level == "error"]


def main() -> int:
    settings = get_settings()
    issues = check(settings)
    prod = is_production(settings)
    print(f"APP_ENV={settings.app_env} (production={prod}) · 점검 {len(issues)}건")
    for i in issues:
        level = i.level if prod else "warn"
        print(f"  [{level:5}] {i.key}: {i.message}")
    if not issues:
        print("  문제 없음")
    return 1 if prod and any(i.level == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
