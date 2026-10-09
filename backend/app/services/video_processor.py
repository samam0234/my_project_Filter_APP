"""짧은 영상: 프레임마다 기존 세그멘터를 쓰고, 검출이 없으면 직전 마스크를 유지한다.

프롬프트에 selector(위치·순서·개수·색)가 있으면 프레임마다 같은 규칙으로 인스턴스를 고른다.
프레임 사이 추적은 하지 않아 사람이 겹치거나 지나가면 선택이 바뀔 수 있다 (광학 흐름·추적은 후속).

출력은 기본 mp4(H.264 + 원본 오디오) — 어디서나 재생된다. OpenCV pip 휠에는 H.264 인코더가 없어(OpenH264 DLL 별도)
프레임은 MJPG 임시 avi 로 쓰고 ffmpeg(imageio-ffmpeg 번들 또는 PATH)로 한 번 변환한다.
ffmpeg 가 없거나 변환이 실패하면 webm(VP8, OpenCV 직접) → 그것도 안 되면 MJPG avi(다운로드 전용)로 내려간다.

블러는 커널 크기가 픽셀 단위라 사진(긴 변 1280px 로 줄여 처리)과 달리 원본 해상도 그대로인 영상에서는
1080p·4K 일수록 흐려지지 않은 것처럼 보인다 → 프레임 크기에 비례해 강도를 보정한다 (_scaled_intensity).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

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


# 형식 이름 → (확장자, OpenCV fourcc, MIME). mp4 는 fourcc 가 없다 — avi 로 쓴 뒤 ffmpeg 로 변환
_FORMATS = {
    "mp4": (".mp4", None, "video/mp4"),
    "webm": (".webm", "VP80", "video/webm"),
    "avi": (".avi", "MJPG", "video/x-msvideo"),
}
MEDIA_TYPES = {ext: mime for ext, _cc, mime in _FORMATS.values()}
BLUR_REFERENCE_SIDE = 1280  # 사진 파이프라인이 처리하는 긴 변 — 이 크기에서 정한 강도를 기준으로 삼는다
MAX_BLUR_INTENSITY = 255


def ffmpeg_exe() -> str | None:
    """PATH 의 ffmpeg 또는 imageio-ffmpeg 번들. 없으면 None."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _to_mp4(tmp_avi: Path, source: Path, dst: Path, ffmpeg: str) -> bool:
    """MJPG avi → H.264 mp4 (+ 원본의 첫 오디오 트랙, 짧은 쪽에 맞춤). 성공 여부."""
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_avi), "-i", str(source),
        "-map", "0:v:0", "-map", "1:a:0?",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:out_range=tv",  # yuv420p 는 짝수 크기만, MJPG 의 full range 는 일반 영상 범위로
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(dst),
    ]
    try:
        done = subprocess.run(cmd, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("mp4 변환 실패: {}", exc)
        return False
    if done.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
        logger.warning("mp4 변환 실패 rc={} {}", done.returncode, done.stderr.decode("utf-8", "replace")[-300:])
        dst.unlink(missing_ok=True)
        return False
    return True


PLAYABLE = {".mp4", ".webm"}  # 브라우저 <video> 가 대부분 재생하는 컨테이너


def preview_mp4(src: Path, dst: Path) -> bool:
    """브라우저가 못 여는 원본(avi · mkv · mov 등)을 작업 기록에서 볼 수 있게 H.264 mp4 로 바꾼다. 성공 여부.

    오디오는 있으면 aac 로. ffmpeg 가 없거나 실패하면 False (원본은 내려받기로만 확인).
    """
    ffmpeg = ffmpeg_exe()
    if ffmpeg is None:
        return False
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
        str(dst),
    ]
    try:
        done = subprocess.run(cmd, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("원본 미리 보기 변환 실패: {}", exc)
        return False
    if done.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
        logger.warning("원본 미리 보기 변환 실패 rc={} {}", done.returncode, done.stderr.decode("utf-8", "replace")[-300:])
        dst.unlink(missing_ok=True)
        return False
    return True


def _scaled_intensity(intensity: int, width: int, height: int) -> int:
    """블러 강도를 프레임 크기에 비례해 키운다 (기준: 긴 변 1280px = 보정 없음, 작은 프레임은 그대로)."""
    factor = max(1.0, max(width, height) / BLUR_REFERENCE_SIDE)
    return int(min(MAX_BLUR_INTENSITY, round(intensity * factor)))


class TemporalSmoother:
    """프레임마다 독립으로 세그한 마스크의 깜빡임(경계 떨림·한두 프레임 빠짐)을 줄인다.

    mode
      "ema"  : 이전 부드러운 마스크와 지수 평균 (움직임을 보정하지 않아 빠른 움직임에서는 꼬리가 남는다)
      "flow" : 광학 흐름(Farneback, 긴 변 FLOW_SIDE 로 줄여 계산)으로 이전 마스크를 현재 프레임 위치로 옮긴 뒤 지수 평균
    장면이 크게 바뀌면(평균 밝기 차 > SCENE_CUT) 기억을 버린다.
    """

    FLOW_SIDE = 320
    SCENE_CUT = 40.0

    def __init__(self, mode: str = "flow", weight: float = 0.6) -> None:
        self.mode = mode
        self.weight = weight  # 현재 프레임 비중
        self._soft: np.ndarray | None = None
        self._gray: np.ndarray | None = None

    def _small_gray(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        scale = min(1.0, self.FLOW_SIDE / max(h, w))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        if scale < 1.0:
            gray = cv2.resize(gray, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        return gray

    def _warp_previous(self, gray: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        """현재 프레임 각 픽셀이 이전 프레임 어디서 왔는지(흐름)를 따라 이전 마스크를 옮긴다."""
        flow = cv2.calcOpticalFlowFarneback(gray, self._gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        sh, sw = gray.shape[:2]
        prev_small = cv2.resize(self._soft, (sw, sh), interpolation=cv2.INTER_LINEAR)
        gx, gy = np.meshgrid(np.arange(sw, dtype=np.float32), np.arange(sh, dtype=np.float32))
        warped = cv2.remap(prev_small, gx + flow[..., 0], gy + flow[..., 1], cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return cv2.resize(warped, size, interpolation=cv2.INTER_LINEAR)

    def update(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """이번 프레임 마스크(0/255) → 부드럽게 한 0/255 마스크."""
        h, w = mask.shape[:2]
        cur = (mask > 127).astype(np.float32)
        gray = self._small_gray(frame) if self.mode == "flow" else None
        reset = self._soft is None or self._soft.shape != cur.shape
        if not reset and gray is not None and self._gray is not None:
            reset = gray.shape != self._gray.shape or float(cv2.absdiff(gray, self._gray).mean()) > self.SCENE_CUT
        if reset:
            soft = cur
        else:
            prev = self._warp_previous(gray, (w, h)) if self.mode == "flow" else self._soft
            soft = self.weight * cur + (1.0 - self.weight) * prev
        self._soft, self._gray = soft, gray
        return np.where(soft >= 0.5, 255, 0).astype(np.uint8)


class FrameRenderer:
    """프레임 한 장 → 효과 결과 (영상 · GIF 공용).

    프레임마다 세그 → selector 로 인스턴스 고르기 → 겹침 덜어내기(사진과 같은 규칙) → 검출이 없으면 직전 마스크 유지
    → 시간 스무딩 → 효과. 블러 강도는 프레임 크기에 맞춰 보정한다.
    render() 는 apply_effects 결과를 그대로 돌려준다 (배경 제거면 BGRA — GIF 는 알파를 투명색으로 쓴다).
    """

    def __init__(self, parsed: ParsedPrompt, segmentor, *, smoothing: str = "flow", smoothing_weight: float = 0.3) -> None:
        self.parsed = parsed
        self.segmentor = segmentor
        self.effect = (parsed.effect or "remove_bg").lower()
        self.smoother = TemporalSmoother(smoothing, smoothing_weight) if smoothing in ("flow", "ema") else None
        self.held = 0  # 검출이 없어 직전 마스크를 다시 쓴 프레임 수
        self._previous: np.ndarray | None = None
        self._scaled: dict[tuple[int, int], ParsedPrompt] = {}

    def _fx_parsed(self, width: int, height: int) -> ParsedPrompt:
        """블러면 프레임 크기에 맞춰 보정한 강도의 ParsedPrompt (크기별 한 번만 만든다)."""
        if self.effect != "blur":
            return self.parsed
        key = (width, height)
        if key not in self._scaled:
            self._scaled[key] = self.parsed.model_copy(
                update={"intensity": _scaled_intensity(self.parsed.intensity, width, height)}
            )
        return self._scaled[key]

    def mask(self, frame: np.ndarray) -> np.ndarray:
        """이 프레임에서 남기거나 지울 대상의 0/255 마스크."""
        parsed = self.parsed
        seg = self.segmentor.predict(frame, targets=list(parsed.target or ["person"]))
        mask = seg.mask
        if seg.instances:
            from app.core.config import get_settings
            from app.services.mask_exclusion import finalize_selection

            chosen = seg.instances
            if parsed.selector is not None:
                chosen = select_instances(seg.instances, parsed.selector, frame).chosen
            mask, _forbid = finalize_selection(seg, chosen, frame.shape[:2], get_settings())
        if mask is None or not np.any(mask):
            if self._previous is not None:
                mask = self._previous
                self.held += 1
        else:
            self._previous = mask.copy()
        if mask is None:
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        if self.smoother is not None and self.effect != "remove_object":
            mask = self.smoother.update(frame, mask)
        return mask

    def render(self, frame: np.ndarray) -> np.ndarray:
        """BGR 프레임 → 효과 결과 (BGR, 배경 제거면 BGRA, 크롭이면 크기가 다를 수 있음)."""
        # 지우기는 프레임마다 학습형 인페인팅을 돌리면 너무 느리다(프레임당 CPU 약 1초) — 영상·GIF 는 Telea
        return apply_effects(frame, self.mask(frame), self._fx_parsed(frame.shape[1], frame.shape[0]), inpaint_engine="telea")


def _open_writer(stem: Path, prefer: str, fps: float, size: tuple[int, int]):
    """prefer 형식부터 시도해 열린 (writer, path, 형식) 을 돌려준다. mp4 는 건너뛴다(별도 변환)."""
    order = [prefer] + [name for name in _FORMATS if name != prefer]
    for name in order:
        if name not in _FORMATS or _FORMATS[name][1] is None:
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
    """보관 폴더의 결과 파일 (mp4 → webm → 예전 avi 순)."""
    for ext, _cc, _mime in _FORMATS.values():
        path = root / f"result{ext}"
        if path.is_file():
            return path
    return None


def _read_frames(src: Path, limit: int):
    """영상 앞에서부터 limit 프레임 (BGR). 지우기 2단계 처리는 이것을 두 번 돈다."""
    capture = cv2.VideoCapture(str(src))
    count = 0
    try:
        while count < limit:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            yield frame
            count += 1
    finally:
        capture.release()


def process_video(
    src: Path,
    dst: Path,
    parsed: ParsedPrompt,
    segmentor,
    *,
    max_frames: int = 240,
    max_seconds: float = 20.0,
    max_side: int = 3840,
    output_format: str = "mp4",
    smoothing: str = "flow",
    smoothing_weight: float = 0.3,
    remove_mode: str = "propagate",
) -> dict:
    """src 를 읽어 dst 확장자를 바꾼 파일(mp4 → 안 되면 webm → avi)로 쓴다.

    대상 지우기(remove_object)는 remove_mode="propagate" 면 영상을 두 번 읽는다 — 1번째에 마스크와 배경판(다른 프레임에서 보인 배경),
    2번째에 그 배경판으로 메운다 (services/video_inpaint). 카메라가 움직이는 영상은 자동으로 프레임마다 Telea.

    반환: frames, held(직전 마스크를 재사용한 프레임 수), fps, path, format, media_type,
    effect · intensity(해석된 효과와 요청 강도 — 화면에 보여 "무엇이 적용됐는지" 확인하게 한다).
    """
    capture = cv2.VideoCapture(str(src))
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없습니다: {src}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    capture.release()
    if max(width, height) > max_side:
        raise ValueError(f"영상 해상도가 너무 큽니다 ({width}×{height}). 긴 변 {max_side}px 이하로 줄여 주세요.")
    if fps <= 1 or fps > 120:
        fps = 15.0
    limit = max(1, int(max_frames))
    if max_seconds > 0:
        limit = min(limit, max(1, int(fps * max_seconds)))

    dst.parent.mkdir(parents=True, exist_ok=True)
    renderer = FrameRenderer(parsed, segmentor, smoothing=smoothing, smoothing_weight=smoothing_weight)
    effect = renderer.effect

    writer = None
    out_path = dst
    ffmpeg = ffmpeg_exe() if output_format == "mp4" else None
    # mp4 는 MJPG 임시 avi 로 쓰고 끝에서 변환, ffmpeg 가 없으면 webm 부터 시도
    write_format = "avi" if ffmpeg else ("webm" if output_format == "mp4" else output_format)
    out_format = write_format
    frames = 0
    plan = None
    if effect == "remove_object" and remove_mode == "propagate":
        from app.services import video_inpaint

        plan = video_inpaint.build_plan(_read_frames(src, limit), renderer.mask)
    try:
        for frame in _read_frames(src, limit):
            if plan is not None:
                rendered = video_inpaint.render(frame, frames, plan)
            else:
                rendered = _as_bgr(renderer.render(frame), frame.shape[1], frame.shape[0])
            if writer is None:
                height, width = rendered.shape[:2]
                writer, out_path, out_format = _open_writer(dst, write_format, fps, (width, height))
                if ffmpeg and out_format == "avi":
                    out_path = dst.with_suffix(".tmp.avi")  # 변환 전 임시 파일 — 변환이 실패하면 이게 곧 결과(avi)
                    writer.release()
                    out_path.unlink(missing_ok=True)
                    dst.with_suffix(".avi").unlink(missing_ok=True)
                    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width, height))
                    if not writer.isOpened():
                        raise ValueError("영상 인코더를 열 수 없습니다.")
            writer.write(rendered)
            frames += 1
    finally:
        if writer is not None:
            writer.release()
    if frames == 0:
        raise ValueError("프레임이 없습니다.")
    if ffmpeg and out_format == "avi":
        final = dst.with_suffix(".mp4")
        if _to_mp4(out_path, src, final, ffmpeg):
            out_path.unlink(missing_ok=True)
            out_path, out_format = final, "mp4"
        else:  # 변환 실패 — 임시 avi 를 결과로 (다운로드 전용)
            final_avi = dst.with_suffix(".avi")
            out_path.replace(final_avi)
            out_path = final_avi
    return {
        "frames": frames,
        "held": renderer.held,
        "fps": fps,
        "path": str(out_path),
        "format": out_format,
        "media_type": MEDIA_TYPES[out_path.suffix],
        "effect": effect,
        "intensity": parsed.intensity,
        # 지우기: 고정 카메라로 보고 배경판을 썼는지 · 지울 자리 중 다른 프레임에서 실제로 보인 비율
        "removal": {"static": plan.static, "seen_ratio": round(plan.seen_ratio, 3)} if plan is not None else None,
    }
