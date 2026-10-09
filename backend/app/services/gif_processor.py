"""움직이는 GIF: 프레임마다 영상과 같은 규칙(FrameRenderer)으로 처리해 다시 GIF 로 묶는다.

- 프레임 간격(duration)·반복(loop)은 원본 그대로 둔다
- 배경 제거는 GIF 의 투명색(1비트)으로 — 알파가 반 이상인 픽셀만 남긴다. 부드러운 경계는 GIF 로는 표현할 수 없어
  같은 프레임으로 움직이는 WebP(8비트 알파, 반투명 경계 유지)도 함께 만든다 — 브라우저·메신저 대부분이 재생한다
- 그 밖의 효과(블러·지우기·크롭)는 불투명 GIF
- 프레임 수는 GIF_MAX_FRAMES 로 자른다 (프레임마다 세그를 돌리므로 처리 시간이 프레임 수에 비례)
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageSequence

from app.schemas.request import ParsedPrompt
from app.services.video_processor import FrameRenderer

GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
TRANSPARENT_INDEX = 255  # 투명색 자리 — 나머지 255색에 프레임 색을 줄여 담는다
ALPHA_CUTOFF = 128
MIN_DURATION_MS = 20  # 0·10ms 프레임은 브라우저가 100ms 로 늘려 재생하므로 원본 속도를 지키려 하한만 둔다


def is_gif(data: bytes) -> bool:
    return data[:6] in GIF_SIGNATURES


@dataclass
class GifFrames:
    frames: list[np.ndarray]  # BGR
    durations: list[int]  # ms
    loop: int  # 0 = 무한 반복
    total: int  # 원본 프레임 수 (잘리기 전)


def read_gif(data: bytes, max_frames: int, max_pixels: int = 4_000_000) -> GifFrames:
    """GIF 바이트 → 합성된 전체 프레임(BGR) 목록. 부분 프레임·처리 방식(disposal)은 Pillow 가 합성한다.

    한 프레임이 max_pixels 를 넘으면 거부한다 (프레임 수 × 픽셀이 메모리에 올라감 — 압축 폭탄 방지).
    """
    try:
        image = Image.open(io.BytesIO(data))
    except Exception as exc:  # Pillow 는 손상 파일에 여러 예외를 낸다
        raise ValueError("GIF 를 열 수 없습니다.") from exc
    if (image.format or "").upper() != "GIF":
        raise ValueError("GIF 파일이 아닙니다.")
    width, height = image.size
    if width <= 0 or height <= 0 or width * height > max_pixels:
        raise ValueError(f"GIF 해상도가 너무 큽니다 ({width}×{height}). 한 프레임 {max_pixels // 1_000_000}MP 이하로 줄여 주세요.")
    frames: list[np.ndarray] = []
    durations: list[int] = []
    total = getattr(image, "n_frames", 1)
    for frame in ImageSequence.Iterator(image):
        if len(frames) >= max(1, max_frames):
            break
        rgba = np.array(frame.convert("RGBA"))
        # 원본이 투명 GIF 면 투명한 곳을 흰 배경으로 깔고 처리한다 (세그 모델은 알파를 모른다)
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
        rgb = (rgba[:, :, :3].astype(np.float32) * alpha + 255.0 * (1.0 - alpha)).astype(np.uint8)
        frames.append(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        durations.append(max(MIN_DURATION_MS, int(frame.info.get("duration", image.info.get("duration", 100)) or 100)))
    if not frames:
        raise ValueError("프레임이 없습니다.")
    loop = int(image.info.get("loop", 0) or 0)
    return GifFrames(frames=frames, durations=durations, loop=loop, total=int(total))


def _to_palette(rendered: np.ndarray, transparent: bool) -> Image.Image:
    """효과 결과(BGR · BGRA) → GIF 프레임(P 모드). transparent 면 알파가 낮은 픽셀을 투명색으로."""
    if rendered.ndim == 2:
        rendered = cv2.cvtColor(rendered, cv2.COLOR_GRAY2BGR)
    if rendered.shape[2] == 4:
        rgb = cv2.cvtColor(rendered[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = rendered[:, :, 3]
    else:
        rgb = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)
        alpha = None
    colors = 255 if transparent else 256
    quantized = Image.fromarray(rgb).quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    if not transparent:
        return quantized
    index = np.array(quantized, dtype=np.uint8)
    if alpha is not None:
        index[alpha < ALPHA_CUTOFF] = TRANSPARENT_INDEX
    palette = (quantized.getpalette() or [])[: TRANSPARENT_INDEX * 3]
    palette += [0] * (768 - len(palette))
    out = Image.fromarray(index, mode="P")
    out.putpalette(palette)
    out.info["transparency"] = TRANSPARENT_INDEX
    return out


def encode_gif(rendered: list[np.ndarray], durations: list[int], loop: int, transparent: bool) -> bytes:
    """프레임 목록 → 움직이는 GIF 바이트. 크기가 다른 프레임(크롭)은 첫 프레임 크기에 맞춘다."""
    if not rendered:
        raise ValueError("프레임이 없습니다.")
    height, width = rendered[0].shape[:2]
    frames = []
    for img in rendered:
        if img.shape[0] != height or img.shape[1] != width:
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        frames.append(_to_palette(img, transparent))
    buf = io.BytesIO()
    options = {
        "save_all": True,
        "append_images": frames[1:],
        "duration": durations[: len(frames)],
        "loop": loop,
        "optimize": False,
    }
    if transparent:
        # 다음 프레임 전에 배경으로 지워야 투명한 곳에 이전 프레임이 남지 않는다
        options.update(transparency=TRANSPARENT_INDEX, disposal=2)
    frames[0].save(buf, format="GIF", **options)
    return buf.getvalue()


def encode_webp(rendered: list[np.ndarray], durations: list[int], loop: int) -> bytes:
    """프레임 목록(BGRA) → 움직이는 WebP. 반투명 경계(깃털 처리한 알파)를 그대로 담는다."""
    height, width = rendered[0].shape[:2]
    frames = []
    for img in rendered:
        if img.shape[0] != height or img.shape[1] != width:
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        if img.ndim == 3 and img.shape[2] == 4:
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA), mode="RGBA"))
        else:
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA"))
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations[: len(frames)],
        loop=loop,
        quality=85,
        method=4,
        exact=False,
    )
    return buf.getvalue()


def process_gif(
    data: bytes,
    parsed: ParsedPrompt,
    segmentor,
    *,
    max_frames: int = 120,
    max_pixels: int = 4_000_000,
    smoothing: str = "flow",
    smoothing_weight: float = 0.3,
    remove_mode: str = "propagate",
) -> dict:
    """GIF 바이트 → 처리된 GIF 바이트와 정보.

    반환: data(bytes), webp(배경 제거일 때 부드러운 경계의 움직이는 WebP bytes, 아니면 None),
          frames(처리한 수), total(원본 프레임 수), held, effect, intensity, transparent
    """
    gif = read_gif(data, max_frames, max_pixels)
    renderer = FrameRenderer(parsed, segmentor, smoothing=smoothing, smoothing_weight=smoothing_weight)
    if renderer.effect == "remove_object" and remove_mode == "propagate":
        # 지우기: 다른 프레임에서 보인 배경으로 메운다 (영상과 같은 방식 — services/video_inpaint)
        from app.services import video_inpaint

        plan = video_inpaint.build_plan(gif.frames, renderer.mask)
        rendered = [video_inpaint.render(frame, i, plan) for i, frame in enumerate(gif.frames)]
    else:
        rendered = [renderer.render(frame) for frame in gif.frames]
    transparent = renderer.effect not in ("blur", "remove_object", "crop", "none")
    out = encode_gif(rendered, gif.durations, gif.loop, transparent)
    webp = None
    if transparent:
        try:
            webp = encode_webp(rendered, gif.durations, gif.loop)
        except Exception:  # libwebp 가 없는 Pillow 빌드 — GIF 만으로도 결과는 완전하다
            webp = None
    return {
        "data": out,
        "webp": webp,
        "frames": len(rendered),
        "total": gif.total,
        "held": renderer.held,
        "effect": renderer.effect,
        "intensity": parsed.intensity,
        "transparent": transparent,
    }
