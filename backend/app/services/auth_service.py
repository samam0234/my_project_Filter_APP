"""계정 규칙: 회원가입 · 로그인(잠금) · 세션 · 아이디 찾기 · 비밀번호 재설정.

보안 원칙
- 로그인 실패는 이유를 구분하지 않는다 ("아이디 또는 비밀번호가 올바르지 않습니다")
- 없는 아이디도 DUMMY_HASH 로 같은 시간만큼 검증 → 응답 시간으로 계정 존재 추측 불가
- 아이디 찾기 · 재설정 요청은 계정이 있든 없든 같은 응답 (메일로만 결과 전달)
- 재설정 코드: 하나만 유효 · 만료 · 시도 횟수 제한 · 재발송 간격. 성공 시 모든 세션 로그아웃
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import passwords as pw
from app.core.config import Settings, get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.mailer import send_mail

RESET_PURPOSE = "password_reset"
GENERIC_FIND_ID = "입력한 이메일로 가입된 계정이 있으면 아이디를 메일로 보냈습니다."
GENERIC_RESET_REQUEST = "입력한 정보와 일치하는 계정이 있으면 인증 코드를 메일로 보냈습니다."
INVALID_CODE = "인증 코드가 올바르지 않거나 만료되었습니다. 코드를 다시 받아 주세요."


class AuthError(Exception):
    """사용자에게 그대로 보여줄 수 있는 인증 오류. status 는 HTTP 코드."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


@dataclass
class SessionIssue:
    user: User
    token: str
    expires_at: datetime


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite 는 tz 정보를 버리므로 naive 값은 UTC 로 본다."""
    if dt is None or dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


class AuthService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.repo = UserRepository(db)

    # ------------------------------------------------------------------ 가입
    def signup(
        self,
        *,
        username: str,
        email: str,
        password: str,
        display_name: str | None,
        user_agent: str | None = None,
    ) -> SessionIssue:
        username = username.strip().lower()
        email = email.strip().lower()
        display_name = (display_name or "").strip() or None

        if not pw.USERNAME_RE.match(username):
            raise AuthError("아이디는 영문 소문자·숫자·밑줄(_) 4~20자로 만들어 주세요.")
        if not pw.EMAIL_RE.match(email) or len(email) > 255:
            raise AuthError("올바른 이메일 주소를 입력해 주세요.")
        problem = pw.password_problem(password)
        if problem:
            raise AuthError(problem)
        if display_name and len(display_name) > 50:
            raise AuthError("이름은 50자 이하로 입력해 주세요.")
        if self.repo.by_username(username):
            raise AuthError("이미 사용 중인 아이디입니다.", status=409)
        if self.repo.by_email(email):
            raise AuthError("이미 가입된 이메일입니다. 아이디 찾기를 이용해 주세요.", status=409)

        try:
            user = self.repo.create(
                username=username,
                email=email,
                password_hash=pw.hash_password(password),
                display_name=display_name,
            )
        except IntegrityError as exc:  # 동시 가입 경합
            self.repo.db.rollback()
            raise AuthError("이미 사용 중인 아이디 또는 이메일입니다.", status=409) from exc
        logger.info("회원가입 user={} username={}", user.id, user.username)
        return self._issue_session(user, user_agent)

    # ---------------------------------------------------------------- 로그인
    def login(self, *, username: str, password: str, user_agent: str | None = None) -> SessionIssue:
        user = self.repo.by_username(username.strip().lower())
        if user is None:
            pw.verify_password(password, pw.DUMMY_HASH)
            raise AuthError("아이디 또는 비밀번호가 올바르지 않습니다.", status=401)

        now = _now()
        locked_until = _aware(user.locked_until)
        if locked_until and locked_until > now:
            minutes = max(1, int((locked_until - now).total_seconds() // 60) + 1)
            raise AuthError(f"로그인 시도가 너무 많습니다. {minutes}분 뒤에 다시 시도해 주세요.", status=429)

        if not pw.verify_password(password, user.password_hash):
            user.failed_logins = (user.failed_logins or 0) + 1
            if user.failed_logins >= self.settings.login_max_failures:
                user.locked_until = now + timedelta(minutes=self.settings.login_lock_minutes)
                user.failed_logins = 0
                logger.warning("로그인 잠금 user={}", user.id)
            self.repo.save(user)
            raise AuthError("아이디 또는 비밀번호가 올바르지 않습니다.", status=401)

        user.failed_logins = 0
        user.locked_until = None
        user.last_login_at = now
        self.repo.save(user)
        return self._issue_session(user, user_agent)

    def _issue_session(self, user: User, user_agent: str | None) -> SessionIssue:
        token = pw.new_session_token()
        expires = _now() + timedelta(hours=self.settings.session_ttl_hours)
        self.repo.purge_expired_sessions(_now())
        self.repo.add_session(
            token_hash=pw.token_digest(token),
            user_id=user.id,
            expires_at=expires,
            user_agent=(user_agent or "")[:255] or None,
        )
        return SessionIssue(user=user, token=token, expires_at=expires)

    # ------------------------------------------------------------------ 세션
    def user_from_token(self, token: str | None) -> Optional[User]:
        if not token:
            return None
        session = self.repo.get_session(pw.token_digest(token))
        if session is None:
            return None
        if _aware(session.expires_at) <= _now():
            self.repo.delete_session(session.id)
            return None
        return self.repo.get(session.user_id)

    def logout(self, token: str | None) -> None:
        if token:
            self.repo.delete_session(pw.token_digest(token))

    # ------------------------------------------------------------ 아이디 찾기
    def find_username(self, email: str) -> str:
        user = self.repo.by_email(email.strip().lower())
        if user is not None:
            send_mail(
                user.email,
                "[컷앤킵] 아이디 안내",
                f"안녕하세요{', ' + user.display_name if user.display_name else ''}.\n\n"
                f"요청하신 컷앤킵 아이디는 다음과 같습니다.\n\n    {user.username}\n\n"
                "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.",
                self.settings,
            )
        return GENERIC_FIND_ID

    # ------------------------------------------------------- 비밀번호 재설정
    def request_password_reset(self, *, username: str, email: str) -> str:
        user = self.repo.by_username(username.strip().lower())
        if user is None or user.email != email.strip().lower():
            return GENERIC_RESET_REQUEST

        now = _now()
        last = self.repo.latest_code(user.id, RESET_PURPOSE)
        if last is not None:
            created = _aware(last.created_at)
            if created and (now - created).total_seconds() < self.settings.auth_code_resend_seconds:
                # 재발송 간격 이내 — 새 코드를 만들지 않지만 응답은 동일
                return GENERIC_RESET_REQUEST

        code = pw.new_code()
        self.repo.replace_code(
            user_id=user.id,
            purpose=RESET_PURPOSE,
            code_hash=pw.code_digest(self.settings.secret_key, user.id, code),
            expires_at=now + timedelta(minutes=self.settings.auth_code_ttl_minutes),
            now=now,
        )
        send_mail(
            user.email,
            "[컷앤킵] 비밀번호 재설정 인증 코드",
            f"비밀번호 재설정 인증 코드: {code}\n\n"
            f"{self.settings.auth_code_ttl_minutes}분 안에 입력해 주세요.\n"
            "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다. 비밀번호는 바뀌지 않습니다.",
            self.settings,
        )
        return GENERIC_RESET_REQUEST

    def reset_password(self, *, username: str, code: str, new_password: str) -> None:
        user = self.repo.by_username(username.strip().lower())
        if user is None:
            raise AuthError(INVALID_CODE)
        problem = pw.password_problem(new_password)
        if problem:
            raise AuthError(problem)

        record = self.repo.active_code(user.id, RESET_PURPOSE)
        now = _now()
        if record is None or _aware(record.expires_at) <= now:
            raise AuthError(INVALID_CODE)
        if record.attempts >= self.settings.auth_code_max_attempts:
            raise AuthError(INVALID_CODE)

        expected = pw.code_digest(self.settings.secret_key, user.id, code.strip())
        if not hmac.compare_digest(expected, record.code_hash):
            record.attempts += 1
            if record.attempts >= self.settings.auth_code_max_attempts:
                record.used_at = now  # 시도 초과 → 코드 폐기
            self.repo.save_code(record)
            raise AuthError(INVALID_CODE)

        record.used_at = now
        self.repo.save_code(record)
        user.password_hash = pw.hash_password(new_password)
        user.failed_logins = 0
        user.locked_until = None
        self.repo.save(user)
        self.repo.delete_user_sessions(user.id)  # 다른 기기 로그인 모두 해제
        logger.info("비밀번호 재설정 user={}", user.id)
