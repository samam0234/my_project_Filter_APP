"""영상 · GIF 의 대상 지우기 — 다른 프레임에서 보인 배경으로 메우기.

사진은 LaMa 로 한 장을 메우지만(services/inpaint), 영상은 프레임마다 LaMa 를 돌리면 프레임당 1초 넘게 걸리고
프레임마다 다르게 메워져 깜빡인다. 그래서 Telea 로 메웠는데, 큰 물체는 번진 얼룩이 남았다.

카메라가 고정이면 지울 대상이 움직이는 동안 **그 뒤의 배경이 다른 프레임에서 보인다**. 그 배경을 모아 "깨끗한 배경판"을 만들고
지운 자리를 배경판으로 채운다. 영상 내내 가려져 한 번도 보이지 않은 곳만 배경판 위에서 LaMa 로 **한 번** 메워 모든 프레임에 같이 쓴다
(없으면 Telea). → 실제 배경이 그대로 돌아오고, 프레임 사이 깜빡임이 없다.

카메라가 움직이면 배경판이 어긋나므로 쓰지 않고 기존처럼 프레임마다 Telea (`static=False`).

1단계 `build_plan(frames, mask_fn)`: 프레임마다 마스크(팽창)를 구해 압축 저장하고, 마스크 밖 픽셀을 배경 누적, 카메라 고정 여부 판정
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


@dataclass
class RemovalPlan:
    shape: tuple[int, int]
    masks: list[np.ndarray] = field(default_factory=list)  # np.packbits 로 압축한 원래 마스크 (팽창 전)
    static: bool = False
    plate: np.ndarray | None = None  # 고정 카메라일 때 다 메운 배경판 (BGR)
    seen_ratio: float = 0.0  # 지울 자리 중 다른 프레임에서 실제로 보인 비율 (나머지는 LaMa/Telea)
    motion: list[float] = field(default_factory=list)

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


def build_plan(
    frames: Iterable[np.ndarray],
    mask_fn: Callable[[np.ndarray], np.ndarray],
    *,
    fill_unseen: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
) -> RemovalPlan:
    """1단계. frames 를 한 번 훑으며 마스크 · 배경 누적 · 카메라 움직임을 본다.

    fill_unseen(plate, hole_mask) → 메운 plate. 기본은 LaMa(있으면) → Telea.
    """
    plan: RemovalPlan | None = None
    sums = counts = None
    prev_gray = prev_small_mask = None
    for frame in frames:
        raw = mask_fn(frame) > 127
        mask = _dilate(raw.astype(np.uint8) * 255)  # 윤곽 잔상까지 지우도록 넓힌 자리
        if plan is None:
            plan = RemovalPlan(shape=mask.shape)
            sums = np.zeros((*mask.shape, 3), np.float32)
            counts = np.zeros(mask.shape, np.uint16)
        plan.masks.append(np.packbits(raw))
        keep = ~mask
        sums[keep] += frame[keep]
        counts[keep] += 1
        gray = _small_gray(frame)
        small_mask = cv2.resize(mask.astype(np.uint8), (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        if prev_gray is not None:
            valid = ~(small_mask | prev_small_mask)
            if valid.mean() > 0.2:
                plan.motion.append(float(np.abs(gray - prev_gray)[valid].mean()))
        prev_gray, prev_small_mask = gray, small_mask
    if plan is None:
        raise ValueError("프레임이 없습니다.")
    if plan.motion:
        plan.static = float(np.median(plan.motion)) < STATIC_MEDIAN and float(np.percentile(plan.motion, 90)) < STATIC_P90
    else:
        plan.static = True  # 한 프레임뿐이면 배경판 = 그 프레임 (결국 한 장 지우기)
    if not plan.static:
        return plan

    union = np.zeros(plan.shape, bool)
    for i in range(len(plan.masks)):
        union |= _dilate(plan.mask(i).astype(np.uint8) * 255)
    seen = counts > 0
    plate = np.zeros((*plan.shape, 3), np.uint8)
    plate[seen] = np.clip(sums[seen] / counts[seen][:, None], 0, 255).astype(np.uint8)
    unseen = ~seen
    plan.seen_ratio = float((union & seen).sum() / max(1, union.sum()))
    if unseen.any():
        fill = fill_unseen or _fill_unseen
        plate = fill(plate, (unseen.astype(np.uint8) * 255))
    plan.plate = plate
    return plan


def _fill_unseen(plate: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """한 번도 보이지 않은 자리를 메운다 — LaMa(사진과 같은 설정)가 있으면 LaMa, 아니면 Telea. 영상 전체에서 한 번만."""
    from app.services.inpaint import lama_inpaint

    filled = lama_inpaint(plate, hole)
    if filled is not None:
        return filled
    return apply_remove_object(plate, hole, engine="telea")


def render(frame: np.ndarray, index: int, plan: RemovalPlan) -> np.ndarray:
    """2단계. 고정 카메라면 배경판으로, 아니면 그 프레임만 Telea 로 메운다."""
    raw = plan.mask(index)
    if not raw.any():
        return frame.copy()
    if not plan.static or plan.plate is None:
        return apply_remove_object(frame, raw.astype(np.uint8) * 255, engine="telea")  # 예전 방식 (팽창은 그 안에서 한 번)
    mask = _dilate(raw.astype(np.uint8) * 255)
    # 경계는 살짝 섞어 배경판과 현재 프레임의 밝기 차가 이음새로 보이지 않게
    alpha = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), BLEND_PX)
    alpha = np.maximum(alpha, mask.astype(np.float32))[..., None]
    out = frame.astype(np.float32) * (1 - alpha) + plan.plate.astype(np.float32) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)
