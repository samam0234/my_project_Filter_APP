"""사용자 · 세션 · 인증 코드 DB 접근 (SQL 은 여기에만).

비즈니스 규칙(비밀번호 검증, 잠금, 코드 발급 정책)은 services/auth_service.py 에 있다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.user import AuthCode, AuthSession, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- users ---
    def get(self, user_id: str) -> Optional[User]:
        return self.db.get(User, user_id)

    def by_username(self, username: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.username == username.lower()))

    def by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
        display_name: str | None,
        terms_agreed_at: datetime | None = None,
    ) -> User:
        user = User(
            id=uuid4().hex,
            username=username.lower(),
            email=email.lower(),
            password_hash=password_hash,
            display_name=display_name,
            terms_agreed_at=terms_agreed_at,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # --- sessions ---
    def add_session(self, *, token_hash: str, user_id: str, expires_at: datetime, user_agent: str | None) -> None:
        self.db.add(
            AuthSession(id=token_hash, user_id=user_id, expires_at=expires_at, user_agent=user_agent)
        )
        self.db.commit()

    def get_session(self, token_hash: str) -> Optional[AuthSession]:
        return self.db.get(AuthSession, token_hash)

    def delete_session(self, token_hash: str) -> None:
        self.db.execute(delete(AuthSession).where(AuthSession.id == token_hash))
        self.db.commit()

    def delete_user_sessions(self, user_id: str) -> None:
        self.db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
        self.db.commit()

    def purge_expired_sessions(self, now: datetime) -> None:
        self.db.execute(delete(AuthSession).where(AuthSession.expires_at < now))
        self.db.commit()

    # --- codes ---
    def latest_code(self, user_id: str, purpose: str) -> Optional[AuthCode]:
        return self.db.scalar(
            select(AuthCode)
            .where(AuthCode.user_id == user_id, AuthCode.purpose == purpose)
            .order_by(AuthCode.created_at.desc(), AuthCode.id.desc())
            .limit(1)
        )

    def active_code(self, user_id: str, purpose: str) -> Optional[AuthCode]:
        """가장 최근의 미사용 코드 (만료 여부는 서비스에서 판단)."""
        return self.db.scalar(
            select(AuthCode)
            .where(
                AuthCode.user_id == user_id,
                AuthCode.purpose == purpose,
                AuthCode.used_at.is_(None),
            )
            .order_by(AuthCode.created_at.desc(), AuthCode.id.desc())
            .limit(1)
        )

    def replace_code(self, *, user_id: str, purpose: str, code_hash: str, expires_at: datetime, now: datetime) -> None:
        """이전 미사용 코드를 무효화하고 새 코드 저장 (코드는 항상 하나만 유효)."""
        self.db.execute(
            update(AuthCode)
            .where(AuthCode.user_id == user_id, AuthCode.purpose == purpose, AuthCode.used_at.is_(None))
            .values(used_at=now)
        )
        self.db.add(AuthCode(user_id=user_id, purpose=purpose, code_hash=code_hash, expires_at=expires_at))
        self.db.commit()

    def save_code(self, code: AuthCode) -> None:
        self.db.add(code)
        self.db.commit()
