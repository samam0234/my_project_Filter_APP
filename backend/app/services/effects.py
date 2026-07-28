"""마스크 정제 및 시각 효과 (블러, 크롭, 배경 제거).

OpenCV 연산의 핵심 모듈. LangGraph effect_applier 노드와
ImageProcessor.run 이 공통으로 사용한다.

원칙:
  - 입력 image/mask 는 가능한 한 복사본에서 작업
  - mask 는 단일 채널 0/255 이진을 가정 (3채널이면 GRAY 변환)
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from app.schemas.request import ParsedPrompt


def refine_mask(mask: np.ndarray, image: np.ndarray | None = None) -> np.ndarray:
    """모폴로지 close + 선택적 GrabCut 정제. 항상 복사본에서 작업.

    1) 이진화
    2) MORPH_CLOSE 로 구멍/끊김 보정
    3) 원본 이미지가 있으면 GrabCut 으로 경계 다듬기 (실패 시 모폴로지만)
    """
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)

    # 타원 커널로 작은 구멍을 메움
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 이미지 있고 마스크 내용 있을 때만 GrabCut
    # (전부 0 이거나 전부 255 면 GrabCut 이득이 거의 없음)
    if image is not None and m.any() and not np.all(m > 0):
        try:
            m = _grabcut_refine(image.copy(), m)
        except Exception:
            pass  # 모폴로지 마스크만 유지
    return m


def _grabcut_refine(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """기존 마스크를 초기값으로 GrabCut 3회 반복.

    GC_PR_BGD / GC_PR_FGD 로 두고 확정 전경 픽셀만 255 로 반환.
    """
    h, w = mask.shape[:2]
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[mask > 0] = cv2.GC_PR_FGD

    # GrabCut 내부 GMM 모델 버퍼 (1x65)
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
    """투명 배경 BGRA 이미지 반환.

    알파 채널에 마스크를 그대로 넣어 전경만 남긴다.
    """
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
    """배경만 블러, 피사체는 선명하게.

    전체 가우시안 블러 후 마스크로 전경/배경을 합성한다.
    intensity 는 커널 크기 힌트 (홀수로 정규화).
    """
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    k = max(1, intensity // 2 * 2 + 1)  # 홀수 커널
    blurred = cv2.GaussianBlur(img, (k, k), 0)
    # 전경: 원본 & 마스크 / 배경: 블러 & 반전마스크
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
    """마스크 bounding rect 기준 크롭 (패딩 포함).

    마스크가 비어 있으면 원본 전체를 그대로 반환한다.
    """
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
    # 패딩을 이미지 경계 안으로 클램프
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
    """구조화 프롬프트에 따라 효과 적용.

    effect:
      - blur      → 배경 블러
      - crop      → 피사체 바운딩 크롭
      - none      → 원본 복사
      - 그 외     → remove_bg (기본)

    parsed.crop 이 True 이고 effect 가 crop 이 아니면,
    주 효과 적용 후 추가로 크롭한다.
    """
    refined = refine_mask(mask, image)
    effect = (parsed.effect or "remove_bg").lower()

    if effect == "blur":
        out = apply_blur(image, refined, intensity=parsed.intensity)
    elif effect == "crop":
        out = apply_crop(image, refined)
    elif effect == "none":
        out = image.copy()
    else:
        # 기본: 배경 제거 (BGRA)
        out = apply_remove_bg(image, refined)

    if parsed.crop and effect != "crop":
        # crop 플래그 시 다른 효과 후 크롭
        # 알파가 있으면 알파를 마스크로 사용
        if out.shape[2] == 4:
            alpha = out[:, :, 3]
            out = apply_crop(out, alpha)
        else:
            out = apply_crop(out, refined)

    return out
