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
    4) GrabCut 결과는 원 마스크 주변 띠 안으로 제한 (떨어진 파편 방지)
    """
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    # 【수동·튜닝】 이진화 임계 127 — soft mask 품질에 따라 조정
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)

    # 【수동·튜닝】 커널 (5,5) · iterations=2 — 구멍 메움 강도
    # 조건: 마스크가 깨지거나 너무 두꺼우면 여기 조정
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 이미지 있고 마스크 내용 있을 때만 GrabCut
    # (전부 0 이거나 전부 255 면 GrabCut 이득이 거의 없음)
    if image is not None and m.any() and not np.all(m > 0):
        try:
            grab = _grabcut_refine(image.copy(), m)
            # GrabCut 은 비슷한 색의 떨어진 영역(다른 사람 안전모 등)까지 전경으로 잡는다.
            # 원 마스크 주변 띠 안으로만 허용해 선택하지 않은 인스턴스 조각을 막는다.
            # 【수동·튜닝】 띠 두께 = 긴 변의 1.5% (최소 7px)
            band = max(7, int(max(m.shape[:2]) * 0.015) // 2 * 2 + 1)
            allowed = cv2.dilate(
                m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band, band)), iterations=1
            )
            m = cv2.bitwise_and(grab, allowed)
        except Exception:
            pass  # 모폴로지 마스크만 유지
    return m


def _grabcut_refine(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """기존 마스크를 초기값으로 GrabCut 3회 반복.

    바깥 GC_PR_BGD / 마스크 GC_PR_FGD / 침식한 안쪽 GC_FGD 로 두고 전경 픽셀만 255 로 반환.
    """
    h, w = mask.shape[:2]
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[mask > 0] = cv2.GC_PR_FGD
    # 마스크 안쪽 핵심부는 확실한 전경으로 고정 → GrabCut 은 경계만 조정
    # (어두운 옷처럼 배경색과 비슷한 부위가 통째로 잘려 나가는 것 방지)
    # 【수동·튜닝】 경계 띠 = 긴 변의 2% (최소 5px)
    k = max(5, int(max(h, w) * 0.02) // 2 * 2 + 1)
    core = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)), iterations=1)
    gc_mask[core > 0] = cv2.GC_FGD

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
    # 【수동·튜닝】 padding 기본 8px — 피사체 가장자리 여백
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


# 【수동·튜닝】 물체 지우기 — 마스크 팽창(가장자리 잔상 제거)·inpaint 반경·작업 해상도
REMOVE_DILATE_RATIO = 0.012  # 이미지 긴 변 대비 팽창 커널 크기
REMOVE_INPAINT_RADIUS = 7
REMOVE_WORK_SIDE = 1024  # 이보다 크면 축소해서 메운 뒤 마스크 영역만 원본에 합성


def apply_remove_object(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """선택 대상을 지우고 주변 배경으로 메운다 (OpenCV Telea inpaint).

    - 마스크를 살짝 팽창해 윤곽 잔상(헤일로)을 같이 지움
    - 큰 이미지는 REMOVE_WORK_SIDE 로 축소해 메운 뒤, 마스크 영역만 업스케일 합성
      (원본의 나머지 픽셀은 그대로 유지)
    한계: 큰 물체는 번진 느낌이 남음 → Phase 2 에서 LaMa 등 학습형 inpaint 로 교체 후보
    """
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    if img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
    if not m.any():
        return img

    h, w = img.shape[:2]
    k = max(3, int(max(h, w) * REMOVE_DILATE_RATIO) // 2 * 2 + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    m = cv2.dilate(m, kernel, iterations=1)

    scale = min(1.0, REMOVE_WORK_SIDE / float(max(h, w)))
    if scale < 1.0:
        sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
        small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA)
        small_m = cv2.resize(m, (sw, sh), interpolation=cv2.INTER_NEAREST)
        filled_small = cv2.inpaint(small, small_m, REMOVE_INPAINT_RADIUS, cv2.INPAINT_TELEA)
        filled = cv2.resize(filled_small, (w, h), interpolation=cv2.INTER_CUBIC)
        out = img.copy()
        out[m > 0] = filled[m > 0]
        return out
    return cv2.inpaint(img, m, REMOVE_INPAINT_RADIUS, cv2.INPAINT_TELEA)


def apply_effects(
    image: np.ndarray,
    mask: np.ndarray,
    parsed: ParsedPrompt,
) -> np.ndarray:
    """구조화 프롬프트에 따라 효과 적용.

    effect:
      - remove_object → 선택 대상 지우기 (inpaint), crop 플래그 무시
      - blur      → 배경 블러
      - crop      → 피사체 바운딩 크롭
      - none      → 원본 복사
      - 그 외     → remove_bg (기본)

    parsed.crop 이 True 이고 effect 가 crop 이 아니면,
    주 효과 적용 후 추가로 크롭한다.
    """
    effect = (parsed.effect or "remove_bg").lower()
    if effect == "remove_object":
        # GrabCut 으로 줄이면 윤곽이 남으므로 원 마스크 + 팽창만 사용
        return apply_remove_object(image, mask)

    refined = refine_mask(mask, image)
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
