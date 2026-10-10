"""리소스 접근 규칙 — 작업·파일·배치는 소유자만, 운영 콘솔 API 는 관리자 또는 이 PC 에서만.

- 남의 작업은 존재 여부도 알리지 않도록 403 대신 404
- 소유자가 없는(user_id NULL) 옛 작업은 사용자 앱에서 보이지 않는다 (콘솔에서만)
- 콘솔: CONSOLE_ADMINS 계정으로 로그인했으면 어디서든, 아니면 loopback 요청만 (CONSOLE_REQUIRE_LOGIN=true 면 loopback 도 로그인 필수)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import current_user_optional
from app.models.job import Job
from app.models.user import User
from app.repositories.job_repository import JobRepository

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def owned_job(db: Session, job_id: str, user: Optional[User]) -> Job:
    """로그인 사용자 본인의 작업. 아니면 404."""
    row = JobRepository(db).get(job_id)
    if row is None or user is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="작업을 찾을 수 없습니다.")
    return row


@dataclass(frozen=True)
class ConsoleActor:
    """콘솔 API 를 부른 주체. reviewer 기록·화면 표시에 쓴다."""

    via: Literal["admin", "local", "open"]
    username: Optional[str] = None

    @property
    def label(self) -> str:
        """검수 기록(reviewed_by)에 남길 이름."""
        return f"admin:{self.username}" if self.username else f"console:{self.via}"


def is_console_admin(user: Optional[User], settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return user is not None and user.username.lower() in settings.console_admin_set


def require_console(
    request: Request,
    user: Optional[User] = Depends(current_user_optional),
) -> ConsoleActor:
    """운영 콘솔 API 가드.

    1) CONSOLE_ADMINS 계정 로그인 → 허용 (원격 배포에서 쓰는 경로)
    2) CONSOLE_ALLOW_REMOTE=true → 누구나 (앞단에서 막았을 때만, 하위 호환)
    3) CONSOLE_REQUIRE_LOGIN=false 이고 loopback → 허용 (로컬 개발)
    그 외: 로그인 안 했으면 401, 관리자가 아니면 403.
    """
    settings = get_settings()
    if is_console_admin(user, settings):
        return ConsoleActor("admin", user.username)
    if settings.console_allow_remote:
        return ConsoleActor("open")
    host = request.client.host if request.client else ""
    if not settings.console_require_login and host in LOOPBACK:
        return ConsoleActor("local")
    if user is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="운영 콘솔 관리자 계정이 아닙니다.")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="운영 콘솔 관리자 로그인이 필요합니다.")
