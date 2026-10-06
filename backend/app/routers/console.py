"""운영 콘솔 전용 API — /api/v1/console/* (작업 조회 · 학습 데이터 검수)

콘솔(:5174)은 아직 인증이 없어 전체 작업을 볼 수 있는 이 API 를 **서버 PC(loopback)에서만** 허용한다
(core/access.require_local_console, CONSOLE_ALLOW_REMOTE 로 해제).
사용자 앱의 /api/v1/jobs 는 로그인 사용자 본인 작업만 돌려준다.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.access import require_local_console
from app.core.config import get_settings
from app.db.learning import get_learning_db, learning_db_mode
from app.db.session import get_db
from app.models.learning_sample import LearningSample
from app.repositories.job_repository import JobRepository
from app.routers.jobs import _to_response
from app.schemas.learning import (
    BulkReviewRequest,
    BulkReviewResponse,
    DeleteResponse,
    LearningSampleList,
    LearningSampleResponse,
    ReviewRequest,
)
from app.schemas.response import JobResponse
from app.services import learning_review
from app.services.learning_review import resolve_file

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


# ------------------------------------------------------------------ 학습 데이터 검수 (학습 DB)
# 승인된 문장 샘플만 RAG 예시 · LoRA 학습에 쓰인다 (services/learning_review)


def _sample_view(row, settings) -> LearningSampleResponse:
    res = LearningSampleResponse.model_validate(row)
    if resolve_file(row.image_path, settings) is not None:
        res.has_image = True
        res.image_url = f"/api/v1/console/learning/samples/{row.id}/image"
    return res


@router.get("/learning/stats")
async def learning_stats(ldb: Session = Depends(get_learning_db)) -> dict:
    """출처·상태·split 별 건수 + 학습 DB 모드."""
    return {
        **learning_review.stats(ldb),
        "learning_db": learning_db_mode(),
        "retrain_min_new": get_settings().lora_retrain_min_new,
    }


@router.get("/learning/samples", response_model=LearningSampleList)
async def learning_samples(
    status: Optional[str] = None,
    source: Optional[str] = None,
    kind: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    ldb: Session = Depends(get_learning_db),
) -> LearningSampleList:
    rows, total = learning_review.list_samples(
        ldb, status=status, source=source, kind=kind, q=q, limit=limit, offset=offset
    )
    settings = get_settings()
    return LearningSampleList(
        items=[_sample_view(r, settings) for r in rows], total=total, limit=limit, offset=offset
    )


@router.post("/learning/samples/bulk", response_model=BulkReviewResponse)
async def learning_bulk_review(body: BulkReviewRequest, ldb: Session = Depends(get_learning_db)) -> BulkReviewResponse:
    return BulkReviewResponse(**learning_review.bulk_review(ldb, body.ids, body.action))


@router.post("/learning/samples/{sample_id}/review", response_model=LearningSampleResponse)
async def learning_review_one(
    sample_id: str, body: ReviewRequest, ldb: Session = Depends(get_learning_db)
) -> LearningSampleResponse:
    try:
        row = learning_review.review(ldb, sample_id, body.action, answer=body.answer, note=body.note)
    except LookupError:
        raise HTTPException(status_code=404, detail="샘플 없음")
    except learning_review.ReviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _sample_view(row, get_settings())


@router.delete("/learning/samples/{sample_id}", response_model=DeleteResponse)
async def learning_delete(sample_id: str, ldb: Session = Depends(get_learning_db)) -> DeleteResponse:
    try:
        return DeleteResponse(**learning_review.delete_sample(ldb, sample_id))
    except LookupError:
        raise HTTPException(status_code=404, detail="샘플 없음")


@router.get("/learning/samples/{sample_id}/image")
async def learning_image(sample_id: str, ldb: Session = Depends(get_learning_db)) -> FileResponse:
    row = ldb.get(LearningSample, sample_id)
    path = resolve_file(row.image_path, get_settings()) if row is not None else None
    if path is None:
        raise HTTPException(status_code=404, detail="이미지 없음")
    return FileResponse(path)
