"""배치 처리 라우터 (Phase 2 스캐폴드) — batch job을 DB에 기록.

현재는 process_batch_stub 으로 상태만 남기고 실제 다중 처리 큐는
Phase 2(Celery/Redis 등) 에서 구현 예정.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.constants import MAX_BATCH_SIZE
from app.db.session import get_db
from app.repositories.batch_repository import BatchRepository
from app.tasks.batch_tasks import process_batch_stub

router = APIRouter(tags=["batch"])


@router.post("/batch")
async def create_batch(
    files: list[UploadFile] = File(...),
    prompt: str = Form(default="person remove background"),
    db: Session = Depends(get_db),
):
    """여러 파일을 한 배치 job 으로 등록.

    - 파일 개수 상한: MAX_BATCH_SIZE
    - 본 처리는 stub (not_implemented 상태 가능)
    - BatchRepository 에 메타만 저장
    """
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max batch size is {MAX_BATCH_SIZE}",
        )
    job_id = uuid4().hex
    # 파일 바이트는 아직 디스크에 안 올리고 파일명 메타만
    items = [{"filename": f.filename, "prompt": prompt} for f in files]
    result = process_batch_stub(job_id, items)
    BatchRepository(db).create(
        batch_id=job_id,
        prompt=prompt,
        total=len(files),
        status=str(result.get("status", "not_implemented")),
        message=str(result.get("message")),
    )
    return result


@router.get("/batch/{job_id}")
async def get_batch_status(job_id: str, db: Session = Depends(get_db)):
    """배치 진행률 조회. 없으면 not_found 스캐폴드 응답."""
    row = BatchRepository(db).get(job_id)
    if row is None:
        return {
            "job_id": job_id,
            "status": "not_found",
            "progress": 0.0,
            "message": "배치 job 없음 (Phase 2 스캐폴드).",
        }
    return {
        "job_id": row.id,
        "status": row.status,
        "progress": row.progress,
        "total": row.total,
        "completed": row.completed,
        "message": row.message,
    }
