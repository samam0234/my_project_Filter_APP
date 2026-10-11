"""계정 라우터 — /api/v1/auth/*

  POST /auth/signup/start    가입 신청 — 메일로 일련번호 발송 (SIGNUP_EMAIL_VERIFICATION 이 꺼져 있으면 바로 가입)
  POST /auth/signup/verify   메일의 일련번호 확인 → 가입 완료 (+ 자동 로그인)
  POST /auth/signup/resend   일련번호 다시 받기
  POST /auth/signup          이메일 인증 없이 바로 가입 — SIGNUP_EMAIL_VERIFICATION=false 일 때만 (켜져 있으면 403)
  POST /auth/login           로그인
  POST /auth/logout          로그아웃 (세션 폐기)
  GET  /auth/me              현재 사용자 (401 이면 비로그인)
  POST /auth/find-id         아이디 찾기 — 이메일로 아이디 발송 (항상 같은 응답)
  POST /auth/password/request 비밀번호 재설정 코드 요청 (항상 같은 응답)
  POST /auth/password/reset  코드 확인 + 새 비밀번호 (모든 세션 로그아웃)
  PATCH /auth/me             표시 이름 수정 (내 계정 화면)
  POST /auth/password/change 현재 비밀번호 확인 후 변경 (다른 기기는 로그아웃)
  POST /auth/logout-all      모든 기기에서 로그아웃
  DELETE /auth/me            스스로 탈퇴 — 작업 · 배치 · 영상 삭제 (비밀번호 + 아이디 확인)

세션 토큰은 HttpOnly · SameSite=Lax 쿠키로만 주고받는다 (JS 에서 읽을 수 없음).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import current_user, session_token, site_url
from app.db.learning import get_learning_db
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccountDelete,
    FindIdRequest,
    LoginRequest,
    MessageResponse,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    SignupRequest,
    SignupResendRequest,
    SignupStartResponse,
    SignupVerifyRequest,
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
    if get_settings().signup_email_verification:
        # 인증 없이 가입하는 길을 열어 두면 이메일 인증이 의미가 없다
        raise HTTPException(status_code=403, detail="이메일 인증이 필요합니다. 가입 신청(/auth/signup/start)을 이용해 주세요.")
    try:
        issue = AuthService(db).signup(
            username=body.username,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            user_agent=request.headers.get("user-agent"),
            agree_terms=body.agree_terms,
        )
    except AuthError as exc:
        _raise(exc)
    _set_session_cookie(response, issue)
    return to_user_response(issue.user)


@router.post("/signup/start", response_model=SignupStartResponse)
def signup_start(body: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    settings = get_settings()
    service = AuthService(db)
    try:
        if not settings.signup_email_verification:
            issue = service.signup(
                username=body.username,
                email=body.email,
                password=body.password,
                display_name=body.display_name,
                user_agent=request.headers.get("user-agent"),
                agree_terms=body.agree_terms,
            )
            _set_session_cookie(response, issue)
            return SignupStartResponse(
                message="가입했습니다.", verification_required=False, user=to_user_response(issue.user)
            )
        pending = service.signup_start(
            username=body.username,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            agree_terms=body.agree_terms,
            site_url=site_url(request),
        )
    except AuthError as exc:
        _raise(exc)
    return SignupStartResponse(
        message="입력한 이메일로 일련번호를 보냈어요. 메일의 [회원가입 인증] 버튼을 눌러 일련번호를 입력해 주세요.",
        verification_required=True,
        email=pending.email,
        expires_minutes=settings.signup_code_ttl_minutes,
        mail_delivered=bool(settings.smtp_host),
    )


@router.post("/signup/verify", response_model=UserResponse, status_code=201)
def signup_verify(body: SignupVerifyRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        issue = AuthService(db).signup_verify(
            email=body.email, code=body.code, user_agent=request.headers.get("user-agent")
        )
    except AuthError as exc:
        _raise(exc)
    _set_session_cookie(response, issue)
    return to_user_response(issue.user)


@router.post("/signup/resend", response_model=SignupStartResponse)
def signup_resend(body: SignupResendRequest, request: Request, db: Session = Depends(get_db)):
    try:
        pending = AuthService(db).signup_resend(email=body.email, site_url=site_url(request))
    except AuthError as exc:
        _raise(exc)
    return SignupStartResponse(
        message="일련번호를 다시 보냈어요. 이전 일련번호는 쓸 수 없어요.",
        verification_required=True,
        email=pending.email,
        expires_minutes=get_settings().signup_code_ttl_minutes,
        mail_delivered=bool(get_settings().smtp_host),
    )


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
def find_id(body: FindIdRequest, request: Request, db: Session = Depends(get_db)):
    return MessageResponse(message=AuthService(db).find_username(body.email, site_url(request)))


@router.post("/password/request", response_model=MessageResponse)
def password_request(body: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    message = AuthService(db).request_password_reset(
        username=body.username, email=body.email, site_url=site_url(request)
    )
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


@router.patch("/me", response_model=UserResponse)
def update_me(body: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        return to_user_response(AuthService(db).update_profile(user, body.display_name))
    except AuthError as exc:
        _raise(exc)


@router.post("/password/change", response_model=MessageResponse)
def password_change(
    body: PasswordChange,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        AuthService(db).change_password(
            user,
            current_password=body.current_password,
            new_password=body.new_password,
            keep_token=session_token(request),
        )
    except AuthError as exc:
        _raise(exc)
    return MessageResponse(message="비밀번호를 바꿨습니다. 다른 기기는 로그아웃됩니다.")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    AuthService(db).logout_all(user)
    _clear_session_cookie(response)
    return MessageResponse(message="모든 기기에서 로그아웃했습니다.")


@router.delete("/me", response_model=MessageResponse)
def delete_me(
    body: AccountDelete,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    ldb: Session = Depends(get_learning_db),
):
    from app.services import user_admin

    try:
        AuthService(db).check_delete(user, password=body.password, confirm=body.confirm)
        user_admin.delete_user(db, ldb, user.id, confirm=user.username)
    except AuthError as exc:
        _raise(exc)
    except user_admin.UserAdminError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message) from exc
    _clear_session_cookie(response)
    return MessageResponse(message="탈퇴했습니다. 작업 · 배치 · 영상은 모두 지웠습니다.")
