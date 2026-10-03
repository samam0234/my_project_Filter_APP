"""단일 이미지 업로드·처리 라우터 (Phase 1).

엔드포인트:
  POST /api/v1/upload          — multipart 파일 + prompt → 파이프라인 실행
  GET  /api/v1/files/{id}/before — 원본 미리보기
  GET  /api/v1/files/{id}/after  — 결과 이미지
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from loguru import logger
from sqlalchemy.orm import Session

from app.core.access import owned_job
from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.security import validate_upload_file
from app.db.session import get_db
from app.exceptions import CutAndKeepError, FileValidationError, to_http_exception
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.response import UploadResponse
from app.workflows.graph import run_pipeline

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(
    file: UploadFile = File(...),
    prompt: str = Form(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> UploadResponse:
    """파일 수신·검증 후 파이프라인 실행.

    로그인:   job 을 DB 에 저장(소유자 연결) · 결과 파일 보관 · before/after 는 파일 URL
    비로그인: 저장하지 않음 — DB 기록·결과 파일·실패 케이스 모두 남기지 않고,
              결과 이미지를 data URL 로 응답에 담아 바로 다운로드만 가능 (saved=false)
    """
    try:
        data = await validate_upload_file(file)
    except FileValidationError as exc:
        raise to_http_exception(exc) from exc

    try:
        # 파이프라인(LLM·YOLO·OpenCV)은 수십 초 걸리는 동기 작업 — 스레드풀에서 돌려
        # 처리 중에도 다른 요청(로그인·작업 기록·헬스)이 바로 응답하게 한다
        result = await run_in_threadpool(
            run_pipeline, image_bytes=data, prompt=prompt, persist=user is not None
        )
        if user is None:
            return _guest_response(result)
        JobRepository(db).save_result(result, prompt=prompt, user_id=user.id)
    except CutAndKeepError as exc:
        raise to_http_exception(exc) from exc
    except Exception as exc:
        logger.exception("업로드 실패")
        raise to_http_exception(CutAndKeepError(str(exc))) from exc

    # 정적 파일 서빙 엔드포인트 경로 (실제 디스크 경로는 result.*_path)
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


def _guest_response(result) -> UploadResponse:
    """비로그인 결과: after 이미지를 data URL 로 담고 디스크 산출물은 즉시 삭제."""
    out_dir = get_settings().upload_path / result.job_id
    after_url = None
    try:
        if result.after_path:
            after = Path(result.after_path)
            mime = "image/png" if after.suffix.lower() == ".png" else "image/jpeg"
            after_url = f"data:{mime};base64," + base64.b64encode(after.read_bytes()).decode("ascii")
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    return UploadResponse(
        job_id=result.job_id,
        status=result.status,
        parsed_prompt=result.parsed_prompt,
        before_url=None,  # 원본은 브라우저가 이미 갖고 있음
        after_url=after_url,
        quality_score=result.quality_score,
        message=result.message,
        feedback_saved=False,
        saved=False,
    )


@router.get("/files/{job_id}/before")
async def get_before(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> FileResponse:
    """처리 전 원본(before.jpg) — 작업 소유자만."""
    from fastapi import HTTPException

    owned_job(db, job_id, user)
    path = get_settings().upload_path / job_id / "before.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="before 이미지 없음")
    return FileResponse(path)


@router.get("/files/{job_id}/after")
async def get_after(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> FileResponse:
    """처리 후 결과 — 작업 소유자만. PNG(배경제거 알파) 우선, 없으면 JPG."""
    from fastapi import HTTPException

    owned_job(db, job_id, user)
    base = get_settings().upload_path / job_id
    for name in ("after.png", "after.jpg"):
        path = base / name
        if path.exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="after 이미지 없음")
