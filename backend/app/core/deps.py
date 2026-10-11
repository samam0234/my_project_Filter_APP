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


def site_url(request: Request) -> str:
    """메일 속 버튼이 열 화면의 기준 주소.

    브라우저가 보낸 Origin 이 허용 목록(CORS_ORIGINS)에 있으면 그것을 쓴다 — 서버 주소와 Cloudflare 같은 앞단 화면
    주소가 여러 개일 때 사용자가 실제로 쓰던 주소로 돌아오게. 목록 밖이면(조작 가능) 목록의 첫 주소, 목록이 비면 개발 주소. 임의 주소로 속여 메일을 보내는 일을 막는다.
    """
    settings = get_settings()
    allowed = settings.cors_origin_list
    origin = (request.headers.get("origin") or "").rstrip("/")
    if origin and origin in allowed:
        return origin
    if allowed:
        return allowed[0].rstrip("/")
    return "http://localhost:5173"


def session_token(request: Request) -> Optional[str]:
    return request.cookies.get(get_settings().session_cookie_name)


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    return AuthService(db).user_from_token(session_token(request))


def current_user(user: Optional[User] = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    return user
