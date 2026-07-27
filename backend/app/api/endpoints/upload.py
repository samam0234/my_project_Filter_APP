"""Single-image upload + process endpoint (Phase 1)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from app.core.security import validate_upload_file
from app.exceptions import CutAndKeepError, FileValidationError, to_http_exception
from app.models.response import UploadResponse
from app.workflows.graph import run_pipeline

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(
    file: UploadFile = File(...),
    prompt: str = Form(..., min_length=1, max_length=1000),
) -> UploadResponse:
    """
    Step 1 of pipeline: receive + validate, then run full LangGraph flow.
    multipart: file + prompt
    """
    try:
        data = await validate_upload_file(file)
    except FileValidationError as exc:
        raise to_http_exception(exc) from exc

    try:
        result = run_pipeline(image_bytes=data, prompt=prompt)
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

    path = get_settings().upload_path / job_id / "before.jpg"
    if not path.exists():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="before image not found")
    return FileResponse(path)


@router.get("/files/{job_id}/after")
async def get_after(job_id: str) -> FileResponse:
    from app.core.config import get_settings

    base = get_settings().upload_path / job_id
    for name in ("after.png", "after.jpg"):
        path = base / name
        if path.exists():
            return FileResponse(path)
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="after image not found")
