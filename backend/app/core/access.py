"""리소스 접근 규칙 — 작업·파일·배치는 소유자만, 운영 콘솔 API 는 이 PC 에서만.

- 남의 작업은 존재 여부도 알리지 않도록 403 대신 404
- 소유자가 없는(user_id NULL) 옛 작업은 사용자 앱에서 보이지 않는다 (콘솔에서만)
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
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


def require_local_console(request: Request) -> None:
    """운영 콘솔 API 가드 — loopback 요청만 (CONSOLE_ALLOW_REMOTE=true 면 해제)."""
    if get_settings().console_allow_remote:
        return
    host = request.client.host if request.client else ""
    if host not in LOOPBACK:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="운영 콘솔 API 는 서버 PC 에서만 사용할 수 있습니다.",
        )
