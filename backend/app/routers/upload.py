"""단일 이미지 업로드·처리 라우터 (Phase 1).

엔드포인트:
  POST /api/v1/upload          — multipart 파일 + prompt → 파이프라인 실행
  GET  /api/v1/files/{id}/before — 원본 (사진 · 영상 · GIF)
  GET  /api/v1/files/{id}/after  — 결과 (사진 · 영상 · GIF)
  GET  /api/v1/files/{id}/thumb  — 작업 기록 썸네일 (영상은 첫 프레임 jpg, 그 밖에는 결과)
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from loguru import logger
from sqlalchemy.orm import Session

from app.core.access import owned_job
from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.ratelimit import enforce, upload_limiter
from app.core.security import validate_upload_file
from app.db.learning import get_learning_db
from app.db.session import get_db
from app.exceptions import CutAndKeepError, FileValidationError, to_http_exception
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.response import UploadResponse
from app.services.learning_catalog import record_request, shared_relpath
from app.workflows.graph import run_pipeline

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    ldb: Session = Depends(get_learning_db),
    user: Optional[User] = Depends(current_user_optional),
) -> UploadResponse:
    """파일 수신·검증 후 파이프라인 실행.

    로그인:   job 을 DB 에 저장(소유자 연결) · 결과 파일 보관 · before/after 는 파일 URL
    비로그인: 저장하지 않음 — DB 기록·결과 파일·실패 케이스 모두 남기지 않고,
              결과 이미지를 data URL 로 응답에 담아 바로 다운로드만 가능 (saved=false)
    """
    settings = get_settings()
    if user is not None:
        enforce(upload_limiter, f"user:{user.id}", settings.upload_rate_member_per_min, "처리 요청")
    else:
        ip = request.client.host if request.client else "unknown"
        enforce(upload_limiter, f"ip:{ip}", settings.upload_rate_guest_per_min,
                "처리 요청 (비로그인은 분당 제한이 더 낮습니다)")

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
        _collect_request(ldb, result, prompt, user.id)
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


def _collect_request(ldb: Session, result, prompt: str, user_id: str) -> None:
    """회원 요청 + 시스템 해석 → 학습 데이터 검수 후보 (운영 콘솔에서 승인되면 LoRA·RAG 에 쓰임).

    학습 DB 문제로 업로드가 실패하면 안 되므로 예외는 로그만 남긴다.
    """
    if not get_settings().learning_collect_requests or result.parsed_prompt is None:
        return
    try:
        record_request(
            ldb,
            job_id=result.job_id,
            prompt=prompt,
            parsed_prompt=result.parsed_prompt.model_dump(),
            user_id=user_id,
            image_path=shared_relpath(result.before_path, get_settings()) if result.before_path else None,
        )
    except Exception:
        ldb.rollback()
        logger.exception("요청 후보 기록 실패 job={}", result.job_id)


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


def _inside_uploads(path: Path) -> bool:
    try:
        path.resolve().relative_to(get_settings().upload_path.resolve())
        return True
    except ValueError:
        return False


def job_file(row, which: str) -> Optional[Path]:
    """작업의 before/after/thumb 파일 경로. 없거나(보관 기간 경과) 업로드 폴더 밖이면 None.

    사진은 예전부터 고정 이름(before.jpg · after.png|jpg)이고, 영상·GIF 는 DB 에 적힌 경로를 쓴다.
    """
    kind = getattr(row, "kind", None) or "image"
    if kind == "image":
        base = get_settings().upload_path / row.id
        names = {"before": ("before.jpg",), "after": ("after.png", "after.jpg"), "thumb": ("after.png", "after.jpg")}
        return next((base / name for name in names[which] if (base / name).is_file()), None)
    if which == "before":
        stored = row.before_path
    elif which == "after" or kind == "gif":  # GIF 썸네일은 결과 GIF 그대로 (움직이는 썸네일)
        stored = row.after_path
    else:  # 영상 썸네일: 처리할 때 만든 첫 프레임
        stored = str(Path(row.after_path).parent / "thumb.jpg") if row.after_path else None
    if not stored:
        return None
    path = Path(stored)
    return path if path.is_file() and _inside_uploads(path) else None


def _serve(job_id: str, which: str, db: Session, user: Optional[User]) -> FileResponse:
    from fastapi import HTTPException

    path = job_file(owned_job(db, job_id, user), which)
    if path is None:
        raise HTTPException(status_code=404, detail=f"{which} 파일 없음")
    return FileResponse(path)


@router.get("/files/{job_id}/before")
async def get_before(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> FileResponse:
    """처리 전 원본 — 작업 소유자만."""
    return _serve(job_id, "before", db, user)


@router.get("/files/{job_id}/after")
async def get_after(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> FileResponse:
    """처리 후 결과 — 작업 소유자만. 사진은 PNG(배경제거 알파) 우선, 없으면 JPG."""
    return _serve(job_id, "after", db, user)


@router.get("/files/{job_id}/thumb")
async def get_thumb(
    job_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(current_user_optional),
) -> FileResponse:
    """작업 기록 썸네일 — 영상은 첫 프레임 jpg, 사진·GIF 는 결과 그대로."""
    return _serve(job_id, "thumb", db, user)
