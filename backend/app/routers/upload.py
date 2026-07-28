"""단일 이미지 업로드·처리 라우터 (Phase 1).

엔드포인트:
  POST /api/v1/upload          — multipart 파일 + prompt → 파이프라인 실행
  GET  /api/v1/files/{id}/before — 원본 미리보기
  GET  /api/v1/files/{id}/after  — 결과 이미지
"""

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
    """파일 수신·검증 후 파이프라인 실행, job을 DB에 저장.

    1) MIME/크기 검증 (validate_upload_file)
    2) run_pipeline (LangGraph 또는 선형)
    3) JobRepository.save_result 로 이력 영속화
    4) before/after URL 을 응답에 포함
    """
    try:
        data = await validate_upload_file(file)
    except FileValidationError as exc:
        raise to_http_exception(exc) from exc

    try:
        # 동기 파이프라인 (CPU/YOLO) — 요청 스레드에서 실행
        result = run_pipeline(image_bytes=data, prompt=prompt)
        JobRepository(db).save_result(result, prompt=prompt)
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


@router.get("/files/{job_id}/before")
async def get_before(job_id: str) -> FileResponse:
    """처리 전 원본(before.jpg) 반환."""
    from app.core.config import get_settings
    from fastapi import HTTPException

    path = get_settings().upload_path / job_id / "before.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="before 이미지 없음")
    return FileResponse(path)


@router.get("/files/{job_id}/after")
async def get_after(job_id: str) -> FileResponse:
    """처리 후 결과. PNG(배경제거 알파) 우선, 없으면 JPG."""
    from app.core.config import get_settings
    from fastapi import HTTPException

    base = get_settings().upload_path / job_id
    for name in ("after.png", "after.jpg"):
        path = base / name
        if path.exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="after 이미지 없음")
