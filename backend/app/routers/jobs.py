"""Job 조회 라우터 — DB에 저장된 처리 이력 조회.

엔드포인트:
  GET /api/v1/jobs/{job_id} — 단건
  GET /api/v1/jobs?limit=&mine= — 최근 목록 (mine=true 는 로그인 사용자 작업만)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.response import JobResponse

router = APIRouter(tags=["jobs"])


def _to_response(row) -> JobResponse:
    """ORM Job 행 → API JobResponse 매핑.

    before/after 는 파일 다운로드 엔드포인트 URL 로 변환한다.
    """
    return JobResponse(
        job_id=row.id,
        prompt=row.prompt,
        status=row.status,
        parsed_prompt=row.parsed_prompt,
        quality_score=row.quality_score or 0.0,
        before_url=f"/api/v1/files/{row.id}/before" if row.before_path else None,
        after_url=f"/api/v1/files/{row.id}/after" if row.after_path else None,
        backend=row.backend,
        message=row.message,
        feedback_saved=bool(row.feedback_saved),
        created_at=row.created_at.isoformat() if row.created_at else None,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    """단건 job 조회. 없으면 404."""
    row = JobRepository(db).get(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job 없음")
    return _to_response(row)


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    limit: int = 50,
    mine: bool = False,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> list[JobResponse]:
    """최근 job 목록. limit 상한 200. mine=true 는 로그인 필요."""
    if mine and user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    rows = JobRepository(db).list_recent(
        limit=min(limit, 200), user_id=user.id if mine and user else None
    )
    return [_to_response(r) for r in rows]
