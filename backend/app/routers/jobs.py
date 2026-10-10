"""Job 조회 라우터 — DB에 저장된 처리 이력 조회.

엔드포인트:
  GET /api/v1/jobs/{job_id} — 단건 (로그인 · 본인 작업만, 아니면 404)
  GET /api/v1/jobs?limit=     — 로그인 사용자 본인 작업 최근 목록 (비로그인 401)
운영 콘솔의 전체 조회는 routers/console.py (이 PC 에서만).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.access import owned_job
from app.core.deps import current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.response import JobResponse

router = APIRouter(tags=["jobs"])


def _to_response(row) -> JobResponse:
    """ORM Job 행 → API JobResponse 매핑.

    before/after 는 파일 다운로드 엔드포인트 URL 로 변환한다.
    """
    kind = getattr(row, "kind", None) or "image"
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
        kind=kind,
        thumb_url=f"/api/v1/files/{row.id}/thumb" if row.after_path else None,
        webp_url=f"/api/v1/files/{row.id}/webp" if kind == "gif" and _has_webp(row) else None,
    )


def _has_webp(row) -> bool:
    from pathlib import Path

    return bool(row.after_path) and Path(row.after_path).with_suffix(".webp").is_file()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> JobResponse:
    """본인 작업 단건. 없거나 남의 작업이면 404."""
    return _to_response(owned_job(db, job_id, user))


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[JobResponse]:
    """로그인 사용자 본인 작업 최근 목록. limit 상한 200."""
    rows = JobRepository(db).list_recent(limit=min(limit, 200), user_id=user.id)
    return [_to_response(r) for r in rows]
