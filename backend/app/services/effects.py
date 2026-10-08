"""마스크 정제 및 시각 효과 (블러, 크롭, 배경 제거).

OpenCV 연산의 핵심 모듈. LangGraph effect_applier 노드가 사용한다.

원칙:
  - 입력 image/mask 는 가능한 한 복사본에서 작업
  - mask 는 단일 채널 0/255 이진을 가정 (3채널이면 GRAY 변환)
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from app.schemas.request import ParsedPrompt


# 【수동·튜닝】 GrabCut 을 마스크 주변 영역(ROI)에서만 — 결과는 어차피 원 마스크 주변 띠로 잘리므로
# 바깥 픽셀은 쓸모가 없고, 전체 이미지 GrabCut 이 요청 시간의 대부분을 차지했다 (scripts/experiments/refine_speed.py)
GRABCUT_ROI = True
GRABCUT_ROI_MARGIN = 0.15  # bbox 크기 대비 여백 (배경 색 모델을 만들 주변부)
GRABCUT_MAX_SIDE = 800  # ROI 긴 변이 이보다 크면 줄여서 GrabCut 후 원래 크기로 (0 = 끔)
GRABCUT_BAND_RATIO = 0.015  # GrabCut 결과를 원 마스크 주변 이 두께(긴 변 대비) 안으로 제한 — 클수록 경계를 더 많이 고친다
GRABCUT_CORE_RATIO = 0.02  # 확실한 전경으로 고정하는 안쪽 핵심부를 만들 때의 침식 두께(긴 변 대비)


def _roi(mask: np.ndarray, band: int) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    mx = max(band * 2, int((x1 - x0) * GRABCUT_ROI_MARGIN))
    my = max(band * 2, int((y1 - y0) * GRABCUT_ROI_MARGIN))
    h, w = mask.shape[:2]
    return max(0, y0 - my), min(h, y1 + my), max(0, x0 - mx), min(w, x1 + mx)


def refine_mask(
    mask: np.ndarray,
    image: np.ndarray | None = None,
    forbid: np.ndarray | None = None,
    use_grabcut: bool | None = None,
) -> np.ndarray:
    """모폴로지 close + 선택적 GrabCut 정제. 항상 복사본에서 작업.

    forbid: 대상으로 가져오면 안 되는 구역(다른 인스턴스) — GrabCut 에 확실한 배경으로 알리고 결과에서도 뺀다.
    use_grabcut: None 이면 설정 MASK_GRABCUT (기본 꺼짐 — 켜면 섞임이 늘고 경계가 나빠졌다, 실험 문서 참고).

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

    if use_grabcut is None:
        from app.core.config import get_settings

        use_grabcut = get_settings().mask_grabcut

    # 이미지 있고 마스크 내용 있을 때만 GrabCut
    # (전부 0 이거나 전부 255 면 GrabCut 이득이 거의 없음)
    if use_grabcut and image is not None and m.any() and not np.all(m > 0):
        try:
            # GrabCut 은 비슷한 색의 떨어진 영역(다른 사람 안전모 등)까지 전경으로 잡는다.
            # 원 마스크 주변 띠 안으로만 허용해 선택하지 않은 인스턴스 조각을 막는다.
            # 【수동·튜닝】 띠 두께 = 긴 변의 1.5% (최소 7px)
            band = max(7, int(max(m.shape[:2]) * GRABCUT_BAND_RATIO) // 2 * 2 + 1)
            if GRABCUT_ROI:
                y0, y1, x0, x1 = _roi(m, band)
                grab = np.zeros_like(m)
                fb = forbid[y0:y1, x0:x1] if forbid is not None else None
                grab[y0:y1, x0:x1] = _grabcut_scaled(image[y0:y1, x0:x1], m[y0:y1, x0:x1], fb)
            else:
                grab = _grabcut_refine(image.copy(), m, forbid)
            allowed = cv2.dilate(
                m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band, band)), iterations=1
            )
            m = cv2.bitwise_and(grab, allowed)
        except Exception:
            pass  # 모폴로지 마스크만 유지
    if forbid is not None:
        m = cv2.bitwise_and(m, cv2.bitwise_not(forbid))
    return m


def upscale_mask(mask: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """작게 세그한 0/255 마스크를 (w, h) 로 키운다 — 선형 보간 후 절반 임계.

    최근접 보간은 확대 배율만큼 계단이 생긴다 (1280 으로 줄여 세그한 4000px 사진이면 3px 계단).
    """
    w, h = size
    if mask.shape[1] == w and mask.shape[0] == h:
        return mask.copy()
    up = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
    return np.where(up >= 128, 255, 0).astype(np.uint8)


# 【수동·튜닝】 경계 부드럽게 — 가우시안 안티앨리어싱 폭(긴 변 대비, 최소 1px).
# 가이드 필터(이미지 경계를 따라 알파를 퍼뜨림)도 시험했지만 잔디처럼 질감 있는 배경에서 반투명 번짐 띠가 생겼다
# (docs/vaildates/edge-tuning-20261008.md). 좁은 가우시안은 계단만 지우고 배경을 끌어오지 않는다.
FEATHER_SIGMA_RATIO = 0.0008  # 긴 변 1920 → 1.5px
FEATHER_SIGMA_MIN = 1.0


def feather_alpha(mask: np.ndarray, image: np.ndarray | None = None) -> np.ndarray:
    """0/255 마스크 → 경계 1~2px 만 0~255 로 부드러운 알파 (안티앨리어싱).

    합성할 때 계단이 사라진다. 경계에서 몇 px 떨어진 안·밖은 255/0 그대로라 구멍·배경 번짐이 없다.
    image 는 크기 기준으로만 쓴다 (없으면 마스크 크기).
    """
    m = mask if mask.ndim == 2 else cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    if not m.any() or m.all():
        return m.copy()
    h, w = (image if image is not None else m).shape[:2]
    sigma = max(FEATHER_SIGMA_MIN, max(h, w) * FEATHER_SIGMA_RATIO)
    soft = cv2.GaussianBlur((m > 127).astype(np.float32), (0, 0), sigma)
    return (np.clip(soft, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def _grabcut_scaled(image: np.ndarray, mask: np.ndarray, forbid: np.ndarray | None = None) -> np.ndarray:
    """긴 변이 GRABCUT_MAX_SIDE 를 넘으면 줄여서 GrabCut → 원래 크기로 되돌림."""
    h, w = mask.shape[:2]
    scale = GRABCUT_MAX_SIDE / max(h, w) if GRABCUT_MAX_SIDE else 1.0
    if scale >= 1.0:
        return _grabcut_refine(image.copy(), mask, forbid)
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    small_img = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    small_mask = cv2.resize(mask, size, interpolation=cv2.INTER_NEAREST)
    small_forbid = cv2.resize(forbid, size, interpolation=cv2.INTER_NEAREST) if forbid is not None else None
    out = _grabcut_refine(small_img, small_mask, small_forbid)
    up = cv2.resize(out, (w, h), interpolation=cv2.INTER_LINEAR)
    return np.where(up >= 128, 255, 0).astype(np.uint8)


def _grabcut_refine(image: np.ndarray, mask: np.ndarray, forbid: np.ndarray | None = None) -> np.ndarray:
    """기존 마스크를 초기값으로 GrabCut 3회 반복.

    바깥 GC_PR_BGD / 마스크 GC_PR_FGD / 침식한 안쪽 GC_FGD 로 두고 전경 픽셀만 255 로 반환.
    """
    h, w = mask.shape[:2]
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[mask > 0] = cv2.GC_PR_FGD
    # 마스크 안쪽 핵심부는 확실한 전경으로 고정 → GrabCut 은 경계만 조정
    # (어두운 옷처럼 배경색과 비슷한 부위가 통째로 잘려 나가는 것 방지)
    # 【수동·튜닝】 경계 띠 = 긴 변의 2% (최소 5px)
    k = max(5, int(max(h, w) * GRABCUT_CORE_RATIO) // 2 * 2 + 1)
    core = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)), iterations=1)
    gc_mask[core > 0] = cv2.GC_FGD
    if forbid is not None:
        # 다른 인스턴스 구역은 확실한 배경 — 색이 비슷한 이웃을 대상으로 끌어오지 못하게 (대상 핵심부는 위에서 이미 확정)
        gc_mask[(forbid > 0) & (core == 0)] = cv2.GC_BGD

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

    전체 가우시안 블러 후 마스크를 알파(0~255)로 전경/배경을 섞는다 — 0/255 마스크면 예전처럼 딱 잘리고,
    feather_alpha 로 부드럽게 한 마스크면 경계가 자연스럽게 이어진다.
    intensity 는 커널 크기 힌트 (홀수로 정규화).
    """
    img = image.copy()
    m = mask.copy()
    if m.ndim == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    k = max(1, intensity // 2 * 2 + 1)  # 홀수 커널
    blurred = cv2.GaussianBlur(img, (k, k), 0)
    a = (m.astype(np.float32) / 255.0)[:, :, None]
    return (img.astype(np.float32) * a + blurred.astype(np.float32) * (1.0 - a) + 0.5).astype(np.uint8)


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


def apply_remove_object(image: np.ndarray, mask: np.ndarray, *, engine: str | None = None) -> np.ndarray:
    """선택 대상을 지우고 주변 배경으로 메운다.

    - 마스크를 살짝 팽창해 윤곽 잔상(헤일로)을 같이 지움
    - engine: "lama"(학습형, 큰 물체도 무늬를 이어 그림 — services/inpaint) · "telea"(OpenCV, 빠르지만 큰 물체는 번짐)
      None 이면 설정 INPAINT_ENGINE (auto = LaMa 모델이 있으면 LaMa). LaMa 가 실패하면 Telea 로 내려간다
    - Telea: 큰 이미지는 REMOVE_WORK_SIDE 로 축소해 메운 뒤, 마스크 영역만 업스케일 합성 (나머지 픽셀은 원본 그대로)
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

    if engine is None:
        from app.core.config import get_settings

        engine = get_settings().inpaint_engine
    if engine in ("auto", "lama"):
        from app.services.inpaint import lama_inpaint

        filled = lama_inpaint(img, m)
        if filled is not None:
            return filled

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
    *,
    refine: bool = True,
    feather: bool = True,
    inpaint_engine: str | None = None,
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

    refine=False: 호출 측이 이미 refine_mask 를 했을 때 (GrabCut 을 두 번 하면 경계가 깎이고 시간도 두 배 —
    docs/vaildates/edge-tuning-20261008.md). feather: 블러·배경 제거의 경계를 부드러운 알파로.
    """
    effect = (parsed.effect or "remove_bg").lower()
    if effect == "remove_object":
        # GrabCut 으로 줄이면 윤곽이 남으므로 원 마스크 + 팽창만 사용
        return apply_remove_object(image, mask, engine=inpaint_engine)

    if refine:
        refined = refine_mask(mask, image)
    else:
        m = mask if mask.ndim == 2 else cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        refined = np.where(m > 127, 255, 0).astype(np.uint8)
    soft = feather_alpha(refined, image) if feather and effect != "crop" and effect != "none" else refined
    if effect == "blur":
        out = apply_blur(image, soft, intensity=parsed.intensity)
    elif effect == "crop":
        out = apply_crop(image, refined)
    elif effect == "none":
        out = image.copy()
    else:
        # 기본: 배경 제거 (BGRA)
        out = apply_remove_bg(image, soft)

    if parsed.crop and effect != "crop":
        # crop 플래그 시 다른 효과 후 크롭
        # 알파가 있으면 알파를 마스크로 사용
        if out.shape[2] == 4:
            alpha = out[:, :, 3]
            out = apply_crop(out, alpha)
        else:
            out = apply_crop(out, refined)

    return out
