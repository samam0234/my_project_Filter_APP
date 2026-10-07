"""짧은 영상: 프레임마다 기존 세그멘터를 쓰고, 검출이 없으면 직전 마스크를 유지한다.

프롬프트에 selector(위치·순서·개수·색)가 있으면 프레임마다 같은 규칙으로 인스턴스를 고른다.
프레임 사이 추적은 하지 않아 사람이 겹치거나 지나가면 선택이 바뀔 수 있다 (광학 흐름·추적은 후속).

출력은 기본 webm(VP8) — 브라우저 <video> 로 바로 재생된다. OpenCV pip 휠에는 H.264 인코더가 없어
(OpenH264 DLL 별도) mp4 는 쓰지 않는다. VP8 인코더를 못 열면 MJPG avi(다운로드 전용)로 내려간다.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.schemas.request import ParsedPrompt
from app.services.effects import apply_effects
from app.services.instance_selector import select_instances
from app.services.segmentation import union_mask


def _as_bgr(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """효과 결과(그레이·BGRA·크롭)를 원본 프레임 크기의 BGR 로 맞춘다."""
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        bgr = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        image = (bgr * alpha).astype(np.uint8)
    if image.shape[1] != width or image.shape[0] != height:
        image = cv2.resize(image, (width, height))
    return image


# (확장자, fourcc, MIME) — 앞에서부터 열리는 것을 쓴다
_FORMATS = {
    "webm": (".webm", "VP80", "video/webm"),
    "avi": (".avi", "MJPG", "video/x-msvideo"),
}
MEDIA_TYPES = {ext: mime for ext, _cc, mime in _FORMATS.values()}


def _open_writer(stem: Path, prefer: str, fps: float, size: tuple[int, int]):
    """prefer 형식부터 시도해 열린 (writer, path, 형식) 을 돌려준다."""
    order = [prefer] + [name for name in _FORMATS if name != prefer]
    for name in order:
        if name not in _FORMATS:
            continue
        ext, fourcc, _mime = _FORMATS[name]
        path = stem.with_suffix(ext)
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*fourcc), fps, size)
        if writer.isOpened():
            return writer, path, name
        writer.release()
        path.unlink(missing_ok=True)
    raise ValueError("영상 인코더를 열 수 없습니다.")


def find_result(root: Path) -> Path | None:
    """보관 폴더의 결과 파일 (webm 우선, 예전 avi 도)."""
    for ext, _cc, _mime in _FORMATS.values():
        path = root / f"result{ext}"
        if path.is_file():
            return path
    return None


def process_video(
    src: Path,
    dst: Path,
    parsed: ParsedPrompt,
    segmentor,
    *,
    max_frames: int = 240,
    max_seconds: float = 20.0,
    output_format: str = "webm",
) -> dict:
    """src 를 읽어 dst 확장자를 바꾼 파일(webm, 안 되면 avi)로 쓴다.

    반환: frames(처리 프레임 수), held(직전 마스크를 재사용한 프레임 수), fps, path, format, media_type.
    """
    capture = cv2.VideoCapture(str(src))
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없습니다: {src}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    if fps <= 1 or fps > 120:
        fps = 15.0
    limit = max(1, int(max_frames))
    if max_seconds > 0:
        limit = min(limit, max(1, int(fps * max_seconds)))

    dst.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    out_path = dst
    out_format = output_format
    previous = None
    frames = 0
    held = 0
    try:
        while frames < limit:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            seg = segmentor.predict(frame, targets=list(parsed.target or ["person"]))
            mask = seg.mask
            if parsed.selector is not None and seg.instances:
                picked = select_instances(seg.instances, parsed.selector, frame)
                mask = union_mask(picked.chosen, frame.shape[:2])
            if mask is None or not np.any(mask):
                if previous is not None:
                    mask = previous
                    held += 1
            else:
                previous = mask.copy()
            if mask is None:
                mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            rendered = _as_bgr(apply_effects(frame, mask, parsed), frame.shape[1], frame.shape[0])
            if writer is None:
                height, width = rendered.shape[:2]
                writer, out_path, out_format = _open_writer(dst, output_format, fps, (width, height))
            writer.write(rendered)
            frames += 1
    finally:
        capture.release()
        if writer is not None:
            writer.release()
    if frames == 0:
        raise ValueError("프레임이 없습니다.")
    return {
        "frames": frames,
        "held": held,
        "fps": fps,
        "path": str(out_path),
        "format": out_format,
        "media_type": MEDIA_TYPES[out_path.suffix],
    }
