"""Batch processing endpoints (Phase 2 scaffold)."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.constants import MAX_BATCH_SIZE
from app.tasks.batch_tasks import process_batch_stub

router = APIRouter(tags=["batch"])


@router.post("/batch")
async def create_batch(
    files: list[UploadFile] = File(...),
    prompt: str = Form(default="person remove background"),
):
    """Phase 2: enqueue up to 500 images. Currently returns not_implemented."""
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max batch size is {MAX_BATCH_SIZE}",
        )
    job_id = uuid4().hex
    items = [{"filename": f.filename, "prompt": prompt} for f in files]
    return process_batch_stub(job_id, items)


@router.get("/batch/{job_id}")
async def get_batch_status(job_id: str):
    """Phase 2: poll batch job progress."""
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "progress": 0.0,
        "message": "Batch status API is Phase 2.",
    }
