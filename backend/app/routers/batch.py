"""배치 처리 라우터. 로그인 회원 전용.

파일을 디스크에 저장하고 상태를 queued 로 남긴 뒤,
Celery(BATCH_USE_CELERY) 또는 프로세스 안 BackgroundTasks 로 한 장씩 처리한다.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.constants import MAX_BATCH_SIZE
from app.core.deps import current_user
from app.core.security import validate_upload_file
from app.db.session import get_db
from app.exceptions import FileValidationError, to_http_exception
from app.models.user import User
from app.repositories.batch_repository import BatchRepository
from app.tasks.batch_tasks import batch_dir, enqueue_batch, run_batch_job, write_manifest

router = APIRouter(tags=["batch"])


@router.post("/batch")
async def create_batch(
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    prompt: str = Form(default="person remove background"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """여러 파일을 한 배치로 등록하고 처리를 시작한다.

    - 파일 개수 상한: MAX_BATCH_SIZE
    - 바이트는 uploads/batches/{job_id}/items 에 저장
    - 응답은 바로 queued. 진행률은 GET /batch/{job_id}
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파일이 없습니다.")
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max batch size is {MAX_BATCH_SIZE}",
        )
    job_id = uuid4().hex
    root = batch_dir(job_id)
    (root / "items").mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    try:
        for index, file in enumerate(files):
            try:
                data = await validate_upload_file(file)
            except FileValidationError as exc:
                raise to_http_exception(exc) from exc
            suffix = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
            rel = f"items/{index:04d}{suffix}"
            (root / rel).write_bytes(data)
            manifest.append(
                {
                    "index": index,
                    "filename": Path(file.filename or rel).name,
                    "relpath": rel,
                }
            )
        write_manifest(job_id, manifest)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    try:
        BatchRepository(db).create(
            user_id=user.id,
            batch_id=job_id,
            prompt=prompt,
            total=len(manifest),
            status="queued",
            message="대기",
        )
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    if not enqueue_batch(job_id):
        background.add_task(run_batch_job, job_id)
    return {
        "job_id": job_id,
        "status": "queued",
        "total": len(manifest),
        "completed": 0,
        "message": "배치가 대기열에 들어갔습니다.",
    }


@router.get("/batch/{job_id}")
async def get_batch_status(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """본인 배치 진행률 조회. 없거나 남의 배치면 not_found."""
    row = BatchRepository(db).get(job_id)
    if row is None or row.user_id != user.id:
        return {
            "job_id": job_id,
            "status": "not_found",
            "progress": 0.0,
            "message": "배치 job 없음.",
        }
    return {
        "job_id": row.id,
        "status": row.status,
        "progress": row.progress,
        "total": row.total,
        "completed": row.completed,
        "message": row.message,
        "item_results": row.item_results or [],
    }
