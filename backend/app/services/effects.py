"""마스크 정제 및 시각 효과 (블러, 크롭, 배경 제거)."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from app.schemas.request import ParsedPrompt


def refine_mask(mask: np.ndarray, image: np.ndarray | None = None) -> np.ndarray:
    """모폴로지 close + 선택적 GrabCut 정제. 항상 복사본에서 작업."""
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 이미지 있고 마스크 내용 있을 때만 GrabCut
    if image is not None and m.any() and not np.all(m > 0):
        try:
            m = _grabcut_refine(image.copy(), m)
        except Exception:
            pass  # 모폴로지 마스크만 유지
    return m


def _grabcut_refine(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape[:2]
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[mask > 0] = cv2.GC_PR_FGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, gc_mask, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)
    result = np.where(
        (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype(np.uint8)
    return result


def apply_remove_bg(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """투명 배경 BGRA 이미지 반환."""
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    if img.shape[2] == 3:
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    else:
        bgra = img.copy()
    bgra[:, :, 3] = m
    return bgra


def apply_blur(
    image: np.ndarray,
    mask: np.ndarray,
    intensity: int = 15,
) -> np.ndarray:
    """배경만 블러, 피사체는 선명하게."""
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    k = max(1, intensity // 2 * 2 + 1)  # 홀수 커널
    blurred = cv2.GaussianBlur(img, (k, k), 0)
    m3 = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
    subject = cv2.bitwise_and(img, m3)
    inv = cv2.bitwise_not(m)
    inv3 = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
    bg = cv2.bitwise_and(blurred, inv3)
    return cv2.add(subject, bg)


def apply_crop(
    image: np.ndarray,
    mask: np.ndarray,
    padding: int = 8,
) -> np.ndarray:
    """마스크 bounding rect 기준 크롭 (패딩 포함)."""
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(m > 0)
    if len(xs) == 0 or len(ys) == 0:
        return img
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    h, w = img.shape[:2]
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(w - 1, x1 + padding)
    y1 = min(h - 1, y1 + padding)
    return img[y0 : y1 + 1, x0 : x1 + 1].copy()


def apply_effects(
    image: np.ndarray,
    mask: np.ndarray,
    parsed: ParsedPrompt,
) -> np.ndarray:
    """구조화 프롬프트에 따라 효과 적용."""
    refined = refine_mask(mask, image)
    effect = (parsed.effect or "remove_bg").lower()

    if effect == "blur":
        out = apply_blur(image, refined, intensity=parsed.intensity)
    elif effect == "crop":
        out = apply_crop(image, refined)
    elif effect == "none":
        out = image.copy()
    else:
        out = apply_remove_bg(image, refined)

    if parsed.crop and effect != "crop":
        # crop 플래그 시 다른 효과 후 크롭
        if out.shape[2] == 4:
            alpha = out[:, :, 3]
            out = apply_crop(out, alpha)
        else:
            out = apply_crop(out, refined)

    return out
