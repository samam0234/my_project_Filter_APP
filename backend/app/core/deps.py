"""FastAPI 의존성: 로그인 사용자.

- current_user_optional : 로그인했으면 User, 아니면 None (업로드·작업 목록 등 공개 API)
- current_user          : 로그인 필수, 없으면 401
세션 토큰은 HttpOnly 쿠키(SESSION_COOKIE_NAME)로만 받는다.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService


def session_token(request: Request) -> Optional[str]:
    return request.cookies.get(get_settings().session_cookie_name)


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    return AuthService(db).user_from_token(session_token(request))


def current_user(user: Optional[User] = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    return user
