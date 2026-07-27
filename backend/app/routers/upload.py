"""Single-image upload + process router (Phase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from app.core.security import validate_upload_file
from app.db.session import get_db
from app.exceptions import CutAndKeepError, FileValidationError, to_http_exception
from app.repositories.job_repository import JobRepository
from app.schemas.response import UploadResponse
from app.workflows.graph import run_pipeline

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(
    file: UploadFile = File(...),
    prompt: str = Form(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Receive + validate file, run pipeline, persist job to DB."""
    try:
        data = await validate_upload_file(file)
    except FileValidationError as exc:
        raise to_http_exception(exc) from exc

    try:
        result = run_pipeline(image_bytes=data, prompt=prompt)
        JobRepository(db).save_result(result, prompt=prompt)
    except CutAndKeepError as exc:
        raise to_http_exception(exc) from exc
    except Exception as exc:
        logger.exception("upload failed")
        raise to_http_exception(CutAndKeepError(str(exc))) from exc

    before_url = (
        f"/api/v1/files/{result.job_id}/before" if result.before_path else None
    )
    after_url = f"/api/v1/files/{result.job_id}/after" if result.after_path else None

    return UploadResponse(
        job_id=result.job_id,
        status=result.status,
        parsed_prompt=result.parsed_prompt,
        before_url=before_url,
        after_url=after_url,
        quality_score=result.quality_score,
        message=result.message,
        feedback_saved=result.feedback_saved,
    )


@router.get("/files/{job_id}/before")
async def get_before(job_id: str) -> FileResponse:
    from app.core.config import get_settings
    from fastapi import HTTPException

    path = get_settings().upload_path / job_id / "before.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="before image not found")
    return FileResponse(path)


@router.get("/files/{job_id}/after")
async def get_after(job_id: str) -> FileResponse:
    from app.core.config import get_settings
    from fastapi import HTTPException

    base = get_settings().upload_path / job_id
    for name in ("after.png", "after.jpg"):
        path = base / name
        if path.exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="after image not found")
