"""영상 업로드.

비로그인: 처리 결과만 응답하고 디스크·DB 에 남기지 않는다.
회원: uploads/videos/{job_id} 에 결과를 두고 본인만 다시 받는다.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from loguru import logger
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.ratelimit import enforce, upload_limiter
from app.models.user import User
from app.services.prompt_llm import parse_prompt_or_heuristic
from app.services.video_processor import process_video

router = APIRouter(tags=["video"])

ALLOWED_VIDEO_EXT = {".mp4", ".avi", ".webm", ".mov", ".mkv"}
ALLOWED_VIDEO_MIME = {
    "video/mp4",
    "video/webm",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "application/octet-stream",
}


def _video_dir(job_id: str) -> Path:
    return get_settings().upload_path / "videos" / job_id


def _run(src: Path, dst: Path, prompt: str) -> dict:
    from app.workflows import nodes

    settings = get_settings()
    parsed = parse_prompt_or_heuristic(prompt, settings)
    return process_video(
        src,
        dst,
        parsed,
        nodes._get_processor().segmentor,  # 프로세스 공용 세그 모델 (요청마다 다시 로드하지 않는다)
        max_frames=settings.video_max_frames,
        max_seconds=settings.video_max_seconds,
    )


@router.post("/video")
async def process_video_upload(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(default="person blur"),
    user: Optional[User] = Depends(current_user_optional),
):
    """영상 한 개를 프레임 세그 후 avi 로 돌려준다."""
    settings = get_settings()
    if user is not None:
        enforce(upload_limiter, f"user:{user.id}", settings.upload_rate_member_per_min, "처리 요청")
    else:
        ip = request.client.host if request.client else "unknown"
        enforce(upload_limiter, f"ip:{ip}", settings.upload_rate_guest_per_min, "처리 요청 (비로그인은 분당 제한이 더 낮습니다)")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(status_code=400, detail=f"허용 확장자: {', '.join(sorted(ALLOWED_VIDEO_EXT))}")
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if mime not in ALLOWED_VIDEO_MIME:
        raise HTTPException(status_code=400, detail="영상 MIME 이 아닙니다.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(data) > settings.video_max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"영상이 최대 크기를 초과합니다: {settings.video_max_upload_mb}MB.")

    if user is None:
        tmp = Path(tempfile.mkdtemp(prefix="cnk-video-"))
        try:
            src = tmp / f"in{ext}"
            dst = tmp / "result.avi"
            src.write_bytes(data)
            info = await run_in_threadpool(_run, src, dst, prompt)
            payload = dst.read_bytes()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("비로그인 영상 처리 실패")
            raise HTTPException(status_code=500, detail="영상 처리에 실패했습니다.") from exc
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return Response(
            content=payload,
            media_type="video/x-msvideo",
            headers={
                "Content-Disposition": "attachment; filename=result.avi",
                "X-Cutnkeep-Frames": str(info["frames"]),
                "X-Cutnkeep-Held": str(info["held"]),
            },
        )

    job_id = uuid4().hex
    root = _video_dir(job_id)
    root.mkdir(parents=True, exist_ok=True)
    src = root / f"in{ext}"
    dst = root / "result.avi"
    src.write_bytes(data)
    try:
        info = await run_in_threadpool(_run, src, dst, prompt)
    except ValueError as exc:
        shutil.rmtree(root, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        shutil.rmtree(root, ignore_errors=True)
        logger.exception("회원 영상 처리 실패")
        raise HTTPException(status_code=500, detail="영상 처리에 실패했습니다.") from exc
    (root / "owner.json").write_text(
        json.dumps({"user_id": user.id}, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "job_id": job_id,
        "status": "ok",
        "frames": info["frames"],
        "held": info["held"],
        "url": f"/api/v1/video/{job_id}",
        "saved": True,
    }


@router.get("/video/{job_id}")
async def get_video(
    job_id: str,
    user: Optional[User] = Depends(current_user_optional),
):
    """회원 본인의 영상 결과. 비로그인·남의 작업은 404."""
    root = _video_dir(job_id)
    meta_path = root / "owner.json"
    result = root / "result.avi"
    if user is None or not meta_path.is_file() or not result.is_file():
        raise HTTPException(status_code=404, detail="영상 없음")
    try:
        owner = json.loads(meta_path.read_text(encoding="utf-8")).get("user_id")
    except json.JSONDecodeError:
        owner = None
    if owner != user.id:
        raise HTTPException(status_code=404, detail="영상 없음")
    return FileResponse(result, media_type="video/x-msvideo", filename="result.avi")
