"""움직이는 GIF 업로드 (작업실 GIF 탭).

POST /api/v1/gif — multipart 파일(.gif) + prompt → 프레임마다 처리한 GIF
  비로그인: 저장하지 않음 — 결과 GIF 를 data URL 로 응답 (saved=false), 사진과 같은 규칙
  회원:     uploads/{job_id}/before.gif · after.gif 로 보관하고 작업 기록(jobs, kind=gif)에 남긴다
"""

from __future__ import annotations

import base64
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.ratelimit import client_ip, enforce, upload_limiter
from app.db.learning import get_learning_db
from app.db.session import get_db
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.routers.video import collect_request
from app.services.gif_processor import is_gif, process_gif
from app.services.prompt_llm import parse_prompt_or_heuristic

router = APIRouter(tags=["gif"])

GIF_MIMES = {"image/gif", "application/octet-stream"}


class GifResponse(BaseModel):
    job_id: str
    status: str
    parsed_prompt: Optional[dict[str, Any]] = None
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    frames: int
    total: int
    held: int
    effect: str
    transparent: bool
    message: Optional[str] = None
    saved: bool
    # 배경 제거일 때만: 반투명 경계를 살린 움직이는 WebP (GIF 는 1비트 투명이라 경계가 거칠다)
    webp_url: Optional[str] = None


def _run(data: bytes, prompt: str) -> dict:
    from app.workflows import nodes

    settings = get_settings()
    parsed = parse_prompt_or_heuristic(prompt, settings)
    info = process_gif(
        data,
        parsed,
        nodes._get_processor().segmentor,  # 프로세스 공용 세그 모델
        max_frames=settings.gif_max_frames,
        max_pixels=settings.gif_max_pixels,
        smoothing=settings.video_temporal_smoothing,
        smoothing_weight=settings.video_smoothing_weight,
    )
    info["parsed"] = parsed.model_dump()
    return info


def _message(info: dict) -> Optional[str]:
    notes = []
    if info["total"] > info["frames"]:
        notes.append(f"프레임이 많아 앞 {info['frames']}개만 처리했어요 (전체 {info['total']}개)")
    if info["held"]:
        notes.append(f"검출이 없어 직전 모양을 유지한 프레임 {info['held']}개")
    return " · ".join(notes) or None


@router.post("/gif", response_model=GifResponse)
async def process_gif_upload(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    ldb: Session = Depends(get_learning_db),
    user: Optional[User] = Depends(current_user_optional),
) -> GifResponse:
    """GIF 한 개를 프레임마다 세그·효과 적용 후 GIF 로 돌려준다 (배경 제거는 투명 GIF)."""
    settings = get_settings()
    if user is not None:
        enforce(upload_limiter, f"user:{user.id}", settings.upload_rate_member_per_min, "처리 요청")
    else:
        ip = client_ip(request)
        enforce(upload_limiter, f"ip:{ip}", settings.upload_rate_guest_per_min, "처리 요청 (비로그인은 분당 제한이 더 낮습니다)")

    name = (file.filename or "").lower()
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if not name.endswith(".gif") or mime not in GIF_MIMES:
        raise HTTPException(status_code=400, detail="GIF 파일(.gif)만 올릴 수 있어요.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail=f"GIF 가 최대 크기를 초과합니다: {settings.max_upload_size_mb}MB.")
    if not is_gif(data):  # 확장자만 바꾼 파일 거부
        raise HTTPException(status_code=400, detail="GIF 형식이 아닙니다.")

    try:
        info = await run_in_threadpool(_run, data, prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("GIF 처리 실패")
        raise HTTPException(status_code=500, detail="GIF 처리에 실패했습니다.") from exc

    job_id = uuid4().hex
    message = _message(info)
    common = dict(
        job_id=job_id,
        status="ok",
        parsed_prompt=info["parsed"],
        frames=info["frames"],
        total=info["total"],
        held=info["held"],
        effect=info["effect"],
        transparent=info["transparent"],
        message=message,
    )
    if user is None:
        after_url = "data:image/gif;base64," + base64.b64encode(info["data"]).decode("ascii")
        webp_url = "data:image/webp;base64," + base64.b64encode(info["webp"]).decode("ascii") if info["webp"] else None
        return GifResponse(**common, before_url=None, after_url=after_url, webp_url=webp_url, saved=False)

    root = settings.upload_path / job_id
    root.mkdir(parents=True, exist_ok=True)
    before, after = root / "before.gif", root / "after.gif"
    before.write_bytes(data)
    after.write_bytes(info["data"])
    if info["webp"]:
        (root / "after.webp").write_bytes(info["webp"])
    JobRepository(db).save_media(
        job_id=job_id,
        kind="gif",
        prompt=prompt,
        user_id=user.id,
        parsed=info["parsed"],
        before_path=str(before),
        after_path=str(after),
        message=message,
    )
    collect_request(ldb, job_id, prompt, info["parsed"], user.id)
    return GifResponse(
        **common,
        before_url=f"/api/v1/files/{job_id}/before",
        after_url=f"/api/v1/files/{job_id}/after",
        webp_url=f"/api/v1/files/{job_id}/webp" if info["webp"] else None,
        saved=True,
    )
