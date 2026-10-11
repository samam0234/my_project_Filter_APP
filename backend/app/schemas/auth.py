"""계정 API 요청·응답 스키마.

형식 검증은 길이 상한 정도만 두고, 사용자에게 보여줄 규칙 메시지(아이디·비밀번호 규칙)는
services/auth_service.py 에서 한국어로 돌려준다 (Pydantic 기본 영문 오류 대신).
"""

from typing import Optional

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str = Field(..., max_length=64)
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)
    # 만 14세 이상 + 이용약관 · 개인정보 처리방침 동의 — true 가 아니면 가입하지 않는다 (동의 시각을 users 에 남긴다)
    agree_terms: bool = False


class SignupVerifyRequest(BaseModel):
    email: str = Field(..., max_length=255)
    code: str = Field(..., max_length=32)  # 메일의 일련번호 (대소문자 · 하이픈 무시)


class SignupResendRequest(BaseModel):
    email: str = Field(..., max_length=255)


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=64)
    password: str = Field(..., max_length=128)


class FindIdRequest(BaseModel):
    email: str = Field(..., max_length=255)


class PasswordResetRequest(BaseModel):
    username: str = Field(..., max_length=64)
    email: str = Field(..., max_length=255)


class PasswordResetConfirm(BaseModel):
    username: str = Field(..., max_length=64)
    code: str = Field(..., max_length=12)
    new_password: str = Field(..., max_length=128)


class ProfileUpdate(BaseModel):
    """내 정보 수정 — 지금은 표시 이름만 (아이디 · 이메일은 바꾸지 않는다)."""

    display_name: Optional[str] = Field(default=None, max_length=100)


class PasswordChange(BaseModel):
    current_password: str = Field(..., max_length=128)
    new_password: str = Field(..., max_length=128)


class AccountDelete(BaseModel):
    """스스로 탈퇴 — 비밀번호와 아이디를 한 번 더 입력받는다."""

    password: str = Field(..., max_length=128)
    confirm: str = Field(..., max_length=64)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str] = None
    created_at: Optional[str] = None


class SignupStartResponse(BaseModel):
    """가입 신청 결과 — 이메일 인증이 필요하면 verification_required, 아니면 바로 가입된 user."""

    ok: bool = True
    message: str
    verification_required: bool
    email: Optional[str] = None
    expires_minutes: Optional[int] = None
    user: Optional[UserResponse] = None


class MessageResponse(BaseModel):
    ok: bool = True
    message: str
