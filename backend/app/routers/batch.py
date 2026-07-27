"""배치 처리 라우터 (Phase 2 스캐폴드) — batch job을 DB에 기록."""

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
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max batch size is {MAX_BATCH_SIZE}",
        )
    job_id = uuid4().hex
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
