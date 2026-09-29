"""계정 라우터 — /api/v1/auth/*

  POST /auth/signup          회원가입 (+ 자동 로그인)
  POST /auth/login           로그인
  POST /auth/logout          로그아웃 (세션 폐기)
  GET  /auth/me              현재 사용자 (401 이면 비로그인)
  POST /auth/find-id         아이디 찾기 — 이메일로 아이디 발송 (항상 같은 응답)
  POST /auth/password/request 비밀번호 재설정 코드 요청 (항상 같은 응답)
  POST /auth/password/reset  코드 확인 + 새 비밀번호 (모든 세션 로그아웃)

세션 토큰은 HttpOnly · SameSite=Lax 쿠키로만 주고받는다 (JS 에서 읽을 수 없음).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import current_user, session_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    FindIdRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignupRequest,
    UserResponse,
)
from app.services.auth_service import AuthError, AuthService, SessionIssue

router = APIRouter(prefix="/auth", tags=["auth"])


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


def _set_session_cookie(response: Response, issue: SessionIssue) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=issue.token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _raise(exc: AuthError) -> None:
    raise HTTPException(status_code=exc.status, detail=exc.message) from exc


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(body: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        issue = AuthService(db).signup(
            username=body.username,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        _raise(exc)
    _set_session_cookie(response, issue)
    return to_user_response(issue.user)


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        issue = AuthService(db).login(
            username=body.username,
            password=body.password,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        _raise(exc)
    _set_session_cookie(response, issue)
    return to_user_response(issue.user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    AuthService(db).logout(session_token(request))
    _clear_session_cookie(response)
    return MessageResponse(message="로그아웃했습니다.")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return to_user_response(user)


@router.post("/find-id", response_model=MessageResponse)
def find_id(body: FindIdRequest, db: Session = Depends(get_db)):
    return MessageResponse(message=AuthService(db).find_username(body.email))


@router.post("/password/request", response_model=MessageResponse)
def password_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    message = AuthService(db).request_password_reset(username=body.username, email=body.email)
    return MessageResponse(message=message)


@router.post("/password/reset", response_model=MessageResponse)
def password_reset(body: PasswordResetConfirm, response: Response, db: Session = Depends(get_db)):
    try:
        AuthService(db).reset_password(
            username=body.username, code=body.code, new_password=body.new_password
        )
    except AuthError as exc:
        _raise(exc)
    _clear_session_cookie(response)
    return MessageResponse(message="비밀번호를 바꿨습니다. 새 비밀번호로 로그인해 주세요.")
