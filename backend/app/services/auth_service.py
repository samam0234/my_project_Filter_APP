"""계정 규칙: 회원가입(이메일 인증) · 로그인(잠금) · 세션 · 아이디 찾기 · 비밀번호 재설정.

보안 원칙
- 로그인 실패는 이유를 구분하지 않는다 ("아이디 또는 비밀번호가 올바르지 않습니다")
- 없는 아이디도 DUMMY_HASH 로 같은 시간만큼 검증 → 응답 시간으로 계정 존재 추측 불가
- 아이디 찾기 · 재설정 요청은 계정이 있든 없든 같은 응답 (메일로만 결과 전달)
- 재설정 코드: 하나만 유효 · 만료 · 시도 횟수 제한 · 재발송 간격. 성공 시 모든 세션 로그아웃
"""

from __future__ import annotations

import hmac
import uuid
from urllib.parse import quote
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import passwords as pw
from app.core.config import Settings, get_settings
from app.models.user import SignupPending, User
from app.repositories.user_repository import UserRepository
from app.services import mail_templates
from app.services.mailer import send_mail

RESET_PURPOSE = "password_reset"
GENERIC_FIND_ID = "입력한 이메일로 가입된 계정이 있으면 아이디를 메일로 보냈습니다."
GENERIC_RESET_REQUEST = "입력한 정보와 일치하는 계정이 있으면 인증 코드를 메일로 보냈습니다."
INVALID_CODE = "인증 코드가 올바르지 않거나 만료되었습니다. 코드를 다시 받아 주세요."
INVALID_SIGNUP_CODE = "일련번호가 올바르지 않거나 만료되었어요. 메일의 일련번호를 다시 확인하거나 새로 받아 주세요."


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
    def _validated_signup(
        self, *, username: str, email: str, password: str, display_name: str | None, agree_terms: bool
    ) -> tuple[str, str, str | None]:
        """가입 입력을 검사하고 (아이디, 이메일, 이름) 으로 정규화한다. 이미 쓰는 아이디 · 이메일이면 409."""
        if not agree_terms:
            raise AuthError("만 14세 이상인지와 이용약관 · 개인정보 처리방침 동의를 확인해 주세요.")
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
        return username, email, display_name

    def _create_user(
        self, *, username: str, email: str, password_hash: str, display_name: str | None, terms_agreed_at: datetime
    ) -> User:
        try:
            user = self.repo.create(
                username=username,
                email=email,
                password_hash=password_hash,
                display_name=display_name,
                terms_agreed_at=terms_agreed_at,
            )
        except IntegrityError as exc:  # 동시 가입 경합
            self.repo.db.rollback()
            raise AuthError("이미 사용 중인 아이디 또는 이메일입니다.", status=409) from exc
        logger.info("회원가입 user={} username={}", user.id, user.username)
        return user

    def signup(
        self,
        *,
        username: str,
        email: str,
        password: str,
        display_name: str | None,
        user_agent: str | None = None,
        agree_terms: bool = False,
    ) -> SessionIssue:
        """이메일 인증 없이 바로 가입 (SIGNUP_EMAIL_VERIFICATION=false 일 때만 라우터가 연다)."""
        username, email, display_name = self._validated_signup(
            username=username, email=email, password=password, display_name=display_name, agree_terms=agree_terms
        )
        user = self._create_user(
            username=username,
            email=email,
            password_hash=pw.hash_password(password),
            display_name=display_name,
            terms_agreed_at=datetime.now(timezone.utc),
        )
        return self._issue_session(user, user_agent)

    # -------------------------------------------------- 가입 이메일 인증
    def _pending(self, email: str) -> Optional[SignupPending]:
        return self.repo.db.query(SignupPending).filter(SignupPending.email == email.strip().lower()).first()

    def _send_signup_mail(self, pending: SignupPending, code: str, site_url: str) -> bool:
        mail = mail_templates.signup_verify(
            code=code,
            verify_url=f"{site_url}/signup/verify?email={quote(pending.email, safe='')}",
            ttl_minutes=self.settings.signup_code_ttl_minutes,
            name=pending.display_name,
        )
        return send_mail(pending.email, mail.subject, mail.text, self.settings, html=mail.html)

    def _check_resend_interval(self, pending: SignupPending) -> None:
        sent = _aware(pending.sent_at)
        if sent:
            wait = self.settings.auth_code_resend_seconds - (_now() - sent).total_seconds()
            if wait > 0:
                raise AuthError(f"방금 메일을 보냈어요. {int(wait) + 1}초 뒤에 다시 받을 수 있어요.", status=429)

    def _code_hash(self, email: str, serial: str) -> str:
        return pw.code_digest(self.settings.secret_key, f"signup:{email}", pw.normalize_serial(serial))

    def signup_start(
        self,
        *,
        username: str,
        email: str,
        password: str,
        display_name: str | None,
        agree_terms: bool,
        site_url: str,
    ) -> SignupPending:
        """가입 신청 — 입력을 검사해 대기 건을 만들고 일련번호 메일을 보낸다. 사용자는 아직 만들어지지 않는다."""
        username, email, display_name = self._validated_signup(
            username=username, email=email, password=password, display_name=display_name, agree_terms=agree_terms
        )
        db = self.repo.db
        now = _now()
        db.query(SignupPending).filter(SignupPending.expires_at < now).delete(synchronize_session=False)
        pending = self._pending(email)
        if pending is not None:
            self._check_resend_interval(pending)
            db.delete(pending)  # 같은 이메일로 다시 신청하면 이전 신청을 교체
            db.flush()

        code = pw.new_serial()
        pending = SignupPending(
            id=uuid.uuid4().hex,
            email=email,
            username=username,
            display_name=display_name,
            password_hash=pw.hash_password(password),
            terms_agreed_at=now,
            code_hash=self._code_hash(email, code),
            attempts=0,
            expires_at=now + timedelta(minutes=self.settings.signup_code_ttl_minutes),
            sent_at=now,
        )
        db.add(pending)
        db.commit()
        if not self._send_signup_mail(pending, code, site_url):
            db.delete(pending)
            db.commit()
            raise AuthError("인증 메일을 보내지 못했어요. 이메일 주소를 확인하고 잠시 뒤 다시 시도해 주세요.", status=503)
        logger.info("가입 인증 메일 발송 username={}", username)
        return pending

    def signup_resend(self, *, email: str, site_url: str) -> SignupPending:
        """일련번호를 새로 만들어 다시 보낸다 (틀린 횟수 초기화 · 유효 시간 연장)."""
        pending = self._pending(email)
        if pending is None:
            raise AuthError("가입 신청을 찾을 수 없어요. 가입을 처음부터 다시 진행해 주세요.", status=404)
        self._check_resend_interval(pending)
        now = _now()
        code = pw.new_serial()
        pending.code_hash = self._code_hash(pending.email, code)
        pending.attempts = 0
        pending.expires_at = now + timedelta(minutes=self.settings.signup_code_ttl_minutes)
        pending.sent_at = now
        self.repo.db.commit()
        if not self._send_signup_mail(pending, code, site_url):
            raise AuthError("인증 메일을 보내지 못했어요. 잠시 뒤 다시 시도해 주세요.", status=503)
        return pending

    def signup_verify(self, *, email: str, code: str, user_agent: str | None = None) -> SessionIssue:
        """메일의 일련번호가 맞으면 계정을 만들고 로그인 상태로 시작한다."""
        db = self.repo.db
        pending = self._pending(email)
        now = _now()
        if pending is None or _aware(pending.expires_at) <= now:
            raise AuthError(INVALID_SIGNUP_CODE)
        if pending.attempts >= self.settings.auth_code_max_attempts:
            raise AuthError(INVALID_SIGNUP_CODE)

        if not hmac.compare_digest(self._code_hash(pending.email, code), pending.code_hash):
            pending.attempts += 1
            db.commit()
            left = self.settings.auth_code_max_attempts - pending.attempts
            if left <= 0:
                raise AuthError(INVALID_SIGNUP_CODE)
            raise AuthError(f"일련번호가 달라요. {left}번 더 틀리면 새로 받아야 해요.")

        # 신청한 뒤 같은 아이디 · 이메일로 먼저 가입한 사람이 있을 수 있다
        if self.repo.by_username(pending.username) or self.repo.by_email(pending.email):
            db.delete(pending)
            db.commit()
            raise AuthError("그 사이 같은 아이디 또는 이메일로 가입한 계정이 있어요. 다시 가입해 주세요.", status=409)
        user = self._create_user(
            username=pending.username,
            email=pending.email,
            password_hash=pending.password_hash,
            display_name=pending.display_name,
            terms_agreed_at=_aware(pending.terms_agreed_at),
        )
        db.delete(pending)
        db.commit()
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

    def logout_all(self, user: User) -> int:
        """모든 기기에서 로그아웃 (현재 기기 포함)."""
        n = len(user.sessions)
        self.repo.delete_user_sessions(user.id)
        return n

    # ------------------------------------------------------------ 내 계정
    def update_profile(self, user: User, display_name: Optional[str]) -> User:
        name = (display_name or "").strip()
        if len(name) > 50:
            raise AuthError("표시 이름은 50자 이하로 입력해 주세요.")
        user.display_name = name or None
        return self.repo.save(user)

    def change_password(self, user: User, *, current_password: str, new_password: str, keep_token: str | None) -> None:
        """현재 비밀번호 확인 후 변경. 지금 쓰는 기기만 로그인을 유지하고 나머지 세션은 끊는다."""
        if not pw.verify_password(current_password, user.password_hash):
            raise AuthError("현재 비밀번호가 올바르지 않습니다.", status=403)
        problem = pw.password_problem(new_password)
        if problem:
            raise AuthError(problem)
        if pw.verify_password(new_password, user.password_hash):
            raise AuthError("새 비밀번호가 현재 비밀번호와 같습니다.")
        user.password_hash = pw.hash_password(new_password)
        self.repo.save(user)
        self.repo.delete_user_sessions(user.id)
        if keep_token:
            self.repo.add_session(
                token_hash=pw.token_digest(keep_token),
                user_id=user.id,
                expires_at=_now() + timedelta(hours=self.settings.session_ttl_hours),
                user_agent=None,
            )
        logger.info("비밀번호 변경 user={}", user.id)

    def check_delete(self, user: User, *, password: str, confirm: str) -> None:
        """탈퇴 전 본인 확인 — 비밀번호 + 아이디 입력. 운영자(CONSOLE_ADMINS)는 콘솔 보호를 위해 스스로 탈퇴할 수 없다."""
        if not pw.verify_password(password, user.password_hash):
            raise AuthError("비밀번호가 올바르지 않습니다.", status=403)
        if confirm.strip().lower() != user.username:
            raise AuthError("확인용 아이디가 일치하지 않습니다.")
        if user.username in self.settings.console_admin_set:
            raise AuthError("운영자 계정은 스스로 탈퇴할 수 없습니다. 먼저 관리자 목록(CONSOLE_ADMINS)에서 빼 주세요.", status=403)

    # ------------------------------------------------------------ 아이디 찾기
    def find_username(self, email: str, site_url: str = "") -> str:
        user = self.repo.by_email(email.strip().lower())
        if user is not None:
            mail = mail_templates.find_id(
                username=user.username, login_url=f"{site_url}/login", name=user.display_name
            )
            send_mail(user.email, mail.subject, mail.text, self.settings, html=mail.html)
        return GENERIC_FIND_ID

    # ------------------------------------------------------- 비밀번호 재설정
    def request_password_reset(self, *, username: str, email: str, site_url: str = "") -> str:
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
        mail = mail_templates.password_reset(
            code=code,
            reset_url=f"{site_url}/find-password",
            ttl_minutes=self.settings.auth_code_ttl_minutes,
            name=user.display_name,
        )
        send_mail(user.email, mail.subject, mail.text, self.settings, html=mail.html)
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
