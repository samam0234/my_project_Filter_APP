"""영상 업로드.

비로그인: 처리 결과만 응답하고 디스크·DB 에 남기지 않는다.
회원: uploads/videos/{job_id} 에 결과를 두고 본인만 다시 받는다. 작업 기록(jobs, kind=video)에도 남겨
     사진과 같은 "작업 기록" 화면에서 다시 보고 받을 수 있다 (썸네일 = 결과 첫 프레임 thumb.jpg).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from loguru import logger
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.ratelimit import client_ip, enforce, upload_limiter
from app.core.security import validate_video_signature
from app.db.learning import get_learning_db
from app.db.session import get_db
from app.exceptions import FileValidationError
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.services.learning_catalog import record_request
from app.services.prompt_llm import parse_prompt_or_heuristic
from app.services.video_processor import MEDIA_TYPES, PLAYABLE, find_result, preview_mp4, process_video

router = APIRouter(tags=["video"])

ALLOWED_VIDEO_EXT = {".mp4", ".avi", ".webm", ".mov", ".mkv"}
def _mime_ok(mime: str) -> bool:
    """브라우저·OS 마다 같은 파일에 다른 MIME 을 붙인다 (.avi → video/avi · video/x-msvideo · video/msvideo ...).
    그래서 video/* 와 octet-stream 이면 받고, 진짜 영상인지는 내용 시그니처(validate_video_signature)로 확인한다."""
    return mime.startswith("video/") or mime == "application/octet-stream"


def _video_dir(job_id: str) -> Path:
    return get_settings().upload_path / "videos" / job_id


THUMB_SIDE = 480


def write_thumb(video: Path, out: Path) -> bool:
    """결과 영상 첫 프레임 → 긴 변 THUMB_SIDE 의 jpg (작업 기록 썸네일). 실패해도 처리는 성공으로 둔다."""
    capture = cv2.VideoCapture(str(video))
    try:
        ok, frame = capture.read()
    finally:
        capture.release()
    if not ok or frame is None:
        return False
    h, w = frame.shape[:2]
    scale = min(1.0, THUMB_SIDE / max(h, w))
    if scale < 1.0:
        frame = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return bool(cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, 85]))


def collect_request(ldb: Session, job_id: str, prompt: str, parsed: dict, user_id: str) -> None:
    """회원 요청 문장 + 해석 → 학습 데이터 검수 후보 (사진과 같은 경로, 이미지 경로는 없음). 실패해도 처리는 성공."""
    if not get_settings().learning_collect_requests:
        return
    try:
        record_request(ldb, job_id=job_id, prompt=prompt, parsed_prompt=parsed, user_id=user_id, image_path=None)
    except Exception:
        ldb.rollback()
        logger.exception("요청 후보 기록 실패 job={}", job_id)


def _run(src: Path, dst: Path, prompt: str) -> dict:
    from app.workflows import nodes

    settings = get_settings()
    parsed = parse_prompt_or_heuristic(prompt, settings)
    info = process_video(
        src,
        dst,
        parsed,
        nodes._get_processor().segmentor,  # 프로세스 공용 세그 모델 (요청마다 다시 로드하지 않는다)
        max_frames=settings.video_max_frames,
        max_seconds=settings.video_max_seconds,
        max_side=settings.video_max_side,
        output_format=settings.video_output_format,
        smoothing=settings.video_temporal_smoothing,
        smoothing_weight=settings.video_smoothing_weight,
        remove_mode=settings.video_remove_mode,
    )
    info["parsed"] = parsed.model_dump()
    return info


@router.post("/video")
async def process_video_upload(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(default="person blur"),
    db: Session = Depends(get_db),
    ldb: Session = Depends(get_learning_db),
    user: Optional[User] = Depends(current_user_optional),
):
    """영상 한 개를 프레임 세그 후 mp4(H.264, ffmpeg 가 없으면 webm → avi)로 돌려준다."""
    settings = get_settings()
    if user is not None:
        enforce(upload_limiter, f"user:{user.id}", settings.upload_rate_member_per_min, "처리 요청")
    else:
        ip = client_ip(request)
        enforce(upload_limiter, f"ip:{ip}", settings.upload_rate_guest_per_min, "처리 요청 (비로그인은 분당 제한이 더 낮습니다)")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(status_code=400, detail=f"허용 확장자: {', '.join(sorted(ALLOWED_VIDEO_EXT))}")
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if not _mime_ok(mime):
        raise HTTPException(status_code=400, detail="영상 파일이 아닙니다.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(data) > settings.video_max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"영상이 최대 크기를 초과합니다: {settings.video_max_upload_mb}MB.")
    try:
        validate_video_signature(data)
    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if user is None:
        tmp = Path(tempfile.mkdtemp(prefix="cnk-video-"))
        try:
            src = tmp / f"in{ext}"
            dst = tmp / "result"
            src.write_bytes(data)
            info = await run_in_threadpool(_run, src, dst, prompt)
            out = Path(info["path"])
            payload = out.read_bytes()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("비로그인 영상 처리 실패")
            raise HTTPException(status_code=500, detail="영상 처리에 실패했습니다.") from exc
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return Response(
            content=payload,
            media_type=info["media_type"],
            headers={
                "Content-Disposition": f"attachment; filename=result{out.suffix}",
                "X-Cutnkeep-Format": info["format"],
                "X-Cutnkeep-Effect": info["effect"],
                "X-Cutnkeep-Intensity": str(info["intensity"]),
                "X-Cutnkeep-Frames": str(info["frames"]),
                "X-Cutnkeep-Held": str(info["held"]),
            },
        )

    job_id = uuid4().hex
    root = _video_dir(job_id)
    root.mkdir(parents=True, exist_ok=True)
    src = root / f"in{ext}"
    dst = root / "result"
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
    result = Path(info["path"])
    await run_in_threadpool(write_thumb, result, root / "thumb.jpg")
    # 작업 기록에서 원본도 재생되게 — avi · mkv · mov 는 브라우저가 못 연다 (원본 파일은 그대로 둔다)
    before = src
    if src.suffix.lower() not in PLAYABLE and await run_in_threadpool(preview_mp4, src, root / "original.mp4"):
        before = root / "original.mp4"
    held_note = f"검출이 없어 직전 모양을 유지한 프레임 {info['held']}개" if info["held"] else None
    JobRepository(db).save_media(
        job_id=job_id,
        kind="video",
        prompt=prompt,
        user_id=user.id,
        parsed=info["parsed"],
        before_path=str(before),
        after_path=str(result),
        message=held_note,
    )
    collect_request(ldb, job_id, prompt, info["parsed"], user.id)
    return {
        "job_id": job_id,
        "status": "ok",
        "frames": info["frames"],
        "held": info["held"],
        "format": info["format"],
        "effect": info["effect"],
        "intensity": info["intensity"],
        "url": f"/api/v1/video/{job_id}",
        "saved": True,
        "parsed_prompt": info["parsed"],
    }


@router.get("/video/{job_id}")
async def get_video(
    job_id: str,
    user: Optional[User] = Depends(current_user_optional),
):
    """회원 본인의 영상 결과. 비로그인·남의 작업은 404."""
    root = _video_dir(job_id)
    meta_path = root / "owner.json"
    result = find_result(root)
    if user is None or not meta_path.is_file() or result is None:
        raise HTTPException(status_code=404, detail="영상 없음")
    try:
        owner = json.loads(meta_path.read_text(encoding="utf-8")).get("user_id")
    except json.JSONDecodeError:
        owner = None
    if owner != user.id:
        raise HTTPException(status_code=404, detail="영상 없음")
    return FileResponse(result, media_type=MEDIA_TYPES[result.suffix], filename=result.name)
