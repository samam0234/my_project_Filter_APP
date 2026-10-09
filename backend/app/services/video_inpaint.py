"""영상 · GIF 의 대상 지우기 — 다른 프레임에서 보인 배경으로 메우기.

사진은 LaMa 로 한 장을 메우지만(services/inpaint), 영상은 프레임마다 LaMa 를 돌리면 프레임당 1초 넘게 걸리고
프레임마다 다르게 메워져 깜빡인다. 그래서 Telea 로 메웠는데, 큰 물체는 번진 얼룩이 남았다.

지울 대상이 움직이는 동안 **그 뒤의 배경이 다른 프레임에서 보인다**. 그 배경을 모아 "깨끗한 배경판"을 만들고
지운 자리를 배경판으로 채운다. 영상 내내 가려져 한 번도 보이지 않은 곳만 배경판 위에서 LaMa 로 **한 번** 메워 모든 프레임에 같이 쓴다
(없으면 Telea). → 실제 배경이 그대로 돌아오고, 프레임 사이 깜빡임이 없다.

카메라에 따라 세 가지 방식 (`plan.mode`):
  static  : 고정 카메라 — 프레임 좌표 그대로 배경을 모은다
  aligned : 카메라가 움직이지만(팬 · 기울임 · 줌) 배경이 한 평면처럼 맞춰지는 경우 — 프레임마다 기준 좌표로 가는
            호모그래피(ORB 특징점 + RANSAC, 대상 자리는 빼고)를 이어 붙여 넓은 캔버스에 배경을 모으고,
            그릴 때 캔버스를 그 프레임으로 되돌려 채운다
  frame   : 맞추기가 안 되면(시차 큰 장면 · 특징점 부족) 예전처럼 프레임마다 Telea

1단계 `build_plan(frames, mask_fn)`: 프레임마다 마스크(팽창)를 구해 압축 저장하고, 마스크 밖 픽셀을 배경 누적, 카메라 판정
2단계 `render(frame, index, plan)`: 프레임 + 그 프레임 마스크 → 지운 결과
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

import cv2
import numpy as np

from app.services.effects import REMOVE_DILATE_RATIO, apply_remove_object

MOTION_SIDE = 160  # 카메라 움직임 판정용 축소 크기 (긴 변)
STATIC_MEDIAN = 6.0  # 마스크 밖 프레임 간 평균 밝기 차의 중앙값이 이 아래면 고정 카메라 (0~255)
STATIC_P90 = 14.0  # 그리고 90 백분위수가 이 아래 (가끔 흔들리는 정도는 허용)
BLEND_PX = 2  # 메운 자리 경계를 부드럽게 (배경판과 현재 프레임의 밝기 차가 이음새로 보이지 않게)

ALIGN_SIDE = 640  # 특징점 찾기용 축소 크기 (긴 변)
ALIGN_FEATURES = 1500
ALIGN_MIN_INLIERS = 25  # 이보다 적게 맞으면 그 프레임 맞추기 실패
ALIGN_MAX_FAIL = 0.1  # 맞추기 실패 프레임이 이 비율을 넘으면 aligned 를 쓰지 않는다
ALIGNED_MEDIAN = 6.0  # 맞춘 뒤 남는 프레임 간 차이 — 고정 카메라와 같은 기준 (시차가 크면 여기서 걸린다)
ALIGNED_P90 = 14.0
ALIGNED_GAIN = 0.6  # 고정 기준을 넘어도 맞춘 뒤 차이가 맞추기 전의 이 비율 아래면 맞춤 방식 (진짜 고정 카메라는 둘이 비슷하다)
CANVAS_PAD = 0.25  # 기준 프레임 둘레로 넓히는 캔버스 여백 (긴 변 비율, 한쪽) — 팬으로 화면 밖에서 들어오는 배경용
ALIGN_MAX_PIXELS = 1920 * 1088  # 이보다 큰 프레임은 맞춤 방식을 쓰지 않는다 (캔버스 누적 메모리: 1080p 약 100MB)


@dataclass
class RemovalPlan:
    shape: tuple[int, int]
    masks: list[np.ndarray] = field(default_factory=list)  # np.packbits 로 압축한 원래 마스크 (팽창 전)
    mode: str = "frame"  # static | aligned | frame
    plate: np.ndarray | None = None  # 다 메운 배경판 (BGR) — static 은 프레임 크기, aligned 는 캔버스 크기
    seen_ratio: float = 0.0  # 지울 자리 중 다른 프레임에서 실제로 보인 비율 (나머지는 LaMa/Telea)
    motion: list[float] = field(default_factory=list)  # 프레임 간 차이 (맞추기 전)
    aligned_motion: list[float] = field(default_factory=list)  # 맞춘 뒤 남는 프레임 간 차이
    homographies: list[np.ndarray] = field(default_factory=list)  # 프레임 → 캔버스 (aligned 일 때)
    align_failures: int = 0

    @property
    def static(self) -> bool:
        """배경판을 쓰는지 (예전 이름 — 응답 · 평가 호환)."""
        return self.mode in ("static", "aligned")

    def mask(self, index: int) -> np.ndarray:
        """그 프레임의 원래 마스크 (bool). 메우는 자리는 _dilate 로 넓혀 쓴다."""
        h, w = self.shape
        return np.unpackbits(self.masks[index], count=h * w).reshape(h, w).astype(bool)


def _dilate(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape[:2]
    k = max(3, int(max(h, w) * REMOVE_DILATE_RATIO) // 2 * 2 + 1)
    return cv2.dilate((mask > 127).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0


def _small_gray(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    scale = min(1.0, MOTION_SIDE / max(h, w))
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(g, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA).astype(np.float32)


class _Aligner:
    """연속 프레임 사이 호모그래피 (대상 자리는 특징점에서 뺀다). 축소 좌표에서 구해 원래 좌표로 바꾼다."""

    def __init__(self, shape: tuple[int, int]) -> None:
        h, w = shape
        self.scale = min(1.0, ALIGN_SIDE / max(h, w))
        self.size = (max(1, int(w * self.scale)), max(1, int(h * self.scale)))
        self.orb = cv2.ORB_create(ALIGN_FEATURES)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.prev = None  # (keypoints, descriptors)
        s = self.scale
        self.S = np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]], np.float64)
        self.S_inv = np.linalg.inv(self.S)

    def step(self, frame: np.ndarray, hole: np.ndarray) -> np.ndarray | None:
        """이 프레임 → 직전 프레임 호모그래피 (원래 좌표). 첫 프레임 · 실패면 None."""
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), self.size, interpolation=cv2.INTER_AREA)
        keep = cv2.resize((~hole).astype(np.uint8) * 255, self.size, interpolation=cv2.INTER_NEAREST)
        kp, des = self.orb.detectAndCompute(gray, keep)
        prev, self.prev = self.prev, (kp, des)
        if prev is None or des is None or prev[1] is None or len(kp) < ALIGN_MIN_INLIERS:
            return None
        pairs = self.matcher.knnMatch(des, prev[1], k=2)
        good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
        if len(good) < ALIGN_MIN_INLIERS:
            return None
        src = np.float32([kp[m.queryIdx].pt for m in good])
        dst = np.float32([prev[0][m.trainIdx].pt for m in good])
        H, inliers = cv2.findHomography(src, dst, cv2.RANSAC, 2.0)
        if H is None or inliers is None or int(inliers.sum()) < ALIGN_MIN_INLIERS:
            return None
        return self.S_inv @ H @ self.S


def build_plan(
    frames: Iterable[np.ndarray],
    mask_fn: Callable[[np.ndarray], np.ndarray],
    *,
    fill_unseen: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
    allow_aligned: bool = True,
) -> RemovalPlan:
    """1단계. frames 를 한 번 훑으며 마스크 · 배경 누적 · 카메라 움직임을 본다.

    fill_unseen(plate, hole_mask) → 메운 plate. 기본은 LaMa(있으면) → Telea.
    """
    plan: RemovalPlan | None = None
    sums = counts = None  # 고정 카메라용 (프레임 좌표)
    csums = ccounts = None  # 맞춤용 (캔버스 좌표)
    aligner: _Aligner | None = None
    to_canvas = None  # 지금 프레임 → 캔버스
    canvas_size = None
    prev_gray = prev_small_mask = None
    for frame in frames:
        raw = mask_fn(frame) > 127
        mask = _dilate(raw.astype(np.uint8) * 255)  # 윤곽 잔상까지 지우도록 넓힌 자리
        if plan is None:
            plan = RemovalPlan(shape=mask.shape)
            h, w = mask.shape
            sums = np.zeros((h, w, 3), np.float32)
            counts = np.zeros((h, w), np.uint16)
            if allow_aligned and h * w <= ALIGN_MAX_PIXELS:
                pad = int(CANVAS_PAD * max(h, w))
                canvas_size = (w + 2 * pad, h + 2 * pad)
                to_canvas = np.array([[1, 0, pad], [0, 1, pad], [0, 0, 1]], np.float64)
                csums = np.zeros((canvas_size[1], canvas_size[0], 3), np.float32)
                ccounts = np.zeros((canvas_size[1], canvas_size[0]), np.uint16)
                aligner = _Aligner((h, w))
        plan.masks.append(np.packbits(raw))
        keep = ~mask
        sums[keep] += frame[keep]
        counts[keep] += 1

        gray = _small_gray(frame)
        small_mask = cv2.resize(mask.astype(np.uint8), (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        step = None
        if aligner is not None:
            step = aligner.step(frame, mask)
            if len(plan.homographies) > 0:
                if step is None:
                    plan.align_failures += 1  # 직전 변환을 그대로 쓴다 (카메라가 잠깐 멈춘 것으로)
                else:
                    to_canvas = plan.homographies[-1] @ step
            plan.homographies.append(to_canvas.copy())
            wf = cv2.warpPerspective(frame, to_canvas, canvas_size, flags=cv2.INTER_LINEAR)
            wk = cv2.warpPerspective(keep.astype(np.uint8), to_canvas, canvas_size, flags=cv2.INTER_NEAREST) > 0
            csums[wk] += wf[wk]
            ccounts[wk] += 1
        if prev_gray is not None:
            valid = ~(small_mask | prev_small_mask)
            if valid.mean() > 0.2:
                plan.motion.append(float(np.abs(gray - prev_gray)[valid].mean()))
                if step is not None:
                    # 직전 프레임을 이 프레임 좌표로 옮겨 남는 차이 — 시차 · 맞추기 오차
                    s = gray.shape[1] / frame.shape[1]
                    S = np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]], np.float64)
                    Hs = S @ np.linalg.inv(step) @ np.linalg.inv(S)
                    moved = cv2.warpPerspective(prev_gray, Hs, (gray.shape[1], gray.shape[0]), flags=cv2.INTER_LINEAR)
                    inside = cv2.warpPerspective(np.ones_like(prev_gray), Hs, (gray.shape[1], gray.shape[0])) > 0.99
                    ok = valid & inside
                    if ok.mean() > 0.2:
                        plan.aligned_motion.append(float(np.abs(gray - moved)[ok].mean()))
        prev_gray, prev_small_mask = gray, small_mask
    if plan is None:
        raise ValueError("프레임이 없습니다.")

    alignable = (
        aligner is not None
        and len(plan.motion) > 0
        and len(plan.aligned_motion) >= 0.8 * len(plan.motion)
        and plan.align_failures <= ALIGN_MAX_FAIL * max(1, len(plan.masks) - 1)
        and float(np.median(plan.aligned_motion)) < ALIGNED_MEDIAN
        and float(np.percentile(plan.aligned_motion, 90)) < ALIGNED_P90
    )
    if not plan.motion:
        plan.mode = "static"  # 한 프레임뿐이면 배경판 = 그 프레임 (결국 한 장 지우기)
    elif float(np.median(plan.motion)) < STATIC_MEDIAN and float(np.percentile(plan.motion, 90)) < STATIC_P90 and not (
        # 고정 기준은 넘었지만 맞추면 차이가 확 줄어든다 = 카메라가 천천히 움직인다 (느린 확대 · 팬) → 맞춤이 낫다
        alignable and float(np.median(plan.aligned_motion)) < ALIGNED_GAIN * float(np.median(plan.motion))
    ):
        plan.mode = "static"
    elif alignable:
        plan.mode = "aligned"
    else:
        plan.mode = "frame"

    fill = fill_unseen or _fill_unseen
    if plan.mode == "static":
        plan.homographies = []
        union = np.zeros(plan.shape, bool)
        for i in range(len(plan.masks)):
            union |= _dilate(plan.mask(i).astype(np.uint8) * 255)
        plan.plate, plan.seen_ratio = _finish_plate(sums, counts, union, fill)
    elif plan.mode == "aligned":
        union = np.zeros((canvas_size[1], canvas_size[0]), bool)
        for i, H in enumerate(plan.homographies):
            hole = _dilate(plan.mask(i).astype(np.uint8) * 255).astype(np.uint8)
            union |= cv2.warpPerspective(hole, H, canvas_size, flags=cv2.INTER_NEAREST) > 0
        plan.plate, plan.seen_ratio = _finish_plate(csums, ccounts, union, fill)
    else:
        plan.homographies = []
    return plan


def _finish_plate(sums, counts, union, fill) -> tuple[np.ndarray, float]:
    """누적한 배경 → 배경판. 지울 자리 중 한 번도 안 보인 곳만 메운다."""
    seen = counts > 0
    plate = np.zeros(sums.shape, np.uint8)
    plate[seen] = np.clip(sums[seen] / counts[seen][:, None], 0, 255).astype(np.uint8)
    seen_ratio = float((union & seen).sum() / max(1, union.sum()))
    unseen = union & ~seen
    if unseen.any():
        plate = fill(plate, unseen.astype(np.uint8) * 255)
    return plate, seen_ratio


def _fill_unseen(plate: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """한 번도 보이지 않은 자리를 메운다 — LaMa(사진과 같은 설정)가 있으면 LaMa, 아니면 Telea. 영상 전체에서 한 번만."""
    from app.services.inpaint import lama_inpaint

    filled = lama_inpaint(plate, hole)
    if filled is not None:
        return filled
    return apply_remove_object(plate, hole, engine="telea")


def render(frame: np.ndarray, index: int, plan: RemovalPlan) -> np.ndarray:
    """2단계. 배경판이 있으면 배경판으로, 없으면 그 프레임만 Telea 로 메운다."""
    raw = plan.mask(index)
    if not raw.any():
        return frame.copy()
    if plan.mode == "frame" or plan.plate is None:
        return apply_remove_object(frame, raw.astype(np.uint8) * 255, engine="telea")  # 예전 방식 (팽창은 그 안에서 한 번)
    mask = _dilate(raw.astype(np.uint8) * 255)
    if plan.mode == "aligned":
        h, w = plan.shape
        plate = cv2.warpPerspective(plan.plate, np.linalg.inv(plan.homographies[index]), (w, h), flags=cv2.INTER_LINEAR)
    else:
        plate = plan.plate
    # 경계는 살짝 섞어 배경판과 현재 프레임의 밝기 차가 이음새로 보이지 않게
    alpha = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), BLEND_PX)
    alpha = np.maximum(alpha, mask.astype(np.float32))[..., None]
    out = frame.astype(np.float32) * (1 - alpha) + plate.astype(np.float32) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)
