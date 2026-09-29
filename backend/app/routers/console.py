"""운영 콘솔 전용 조회 API — /api/v1/console/*

콘솔(:5174)은 아직 인증이 없어 전체 작업을 볼 수 있는 이 API 를 **서버 PC(loopback)에서만** 허용한다
(core/access.require_local_console, CONSOLE_ALLOW_REMOTE 로 해제).
사용자 앱의 /api/v1/jobs 는 로그인 사용자 본인 작업만 돌려준다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.access import require_local_console
from app.core.config import get_settings
from app.db.session import get_db
from app.repositories.job_repository import JobRepository
from app.routers.jobs import _to_response
from app.schemas.response import JobResponse

router = APIRouter(prefix="/console", tags=["console"], dependencies=[Depends(require_local_console)])


def _console_view(row) -> JobResponse:
    """사용자용 파일 URL(/files, 소유자 전용) 대신 콘솔 전용 파일 URL 로 바꾼다."""
    res = _to_response(row)
    if res.before_url:
        res.before_url = f"/api/v1/console/files/{row.id}/before"
    if res.after_url:
        res.after_url = f"/api/v1/console/files/{row.id}/after"
    return res


@router.get("/jobs", response_model=list[JobResponse])
async def console_jobs(limit: int = 50, db: Session = Depends(get_db)) -> list[JobResponse]:
    """전체 작업 최근 목록 (소유자 무관). limit 상한 200."""
    return [_console_view(r) for r in JobRepository(db).list_recent(limit=min(limit, 200))]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def console_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    row = JobRepository(db).get(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job 없음")
    return _console_view(row)


@router.get("/files/{job_id}/{kind}")
async def console_file(job_id: str, kind: str) -> FileResponse:
    """작업 before/after 파일 (소유자 무관)."""
    base = get_settings().upload_path / job_id
    names = {"before": ("before.jpg",), "after": ("after.png", "after.jpg")}.get(kind)
    if names is None or "/" in job_id or "\\" in job_id or ".." in job_id:
        raise HTTPException(status_code=404, detail="파일 없음")
    for name in names:
        path = base / name
        if path.exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="파일 없음")
