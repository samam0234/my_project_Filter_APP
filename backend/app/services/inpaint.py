"""대상 지우기(remove_object)의 빈자리 메우기 — 학습형 LaMa(ONNX) · 실패하면 OpenCV Telea.

Telea 는 테두리 색을 안쪽으로 번지게 칠할 뿐이라 큰 물체(사람·차·건물)를 지우면 뭉개진 얼룩이 남았다.
LaMa(big-lama, Apache-2.0, Carve/LaMa-ONNX 의 lama_fp32.onnx)는 주변 무늬·구조를 이어 그린다.

- 입력 크기가 512×512 로 고정이라, 마스크 주변을 여유(CONTEXT)만큼 넓혀 잘라 512 로 줄여 넣고 결과를 원래 크기로 되돌린 뒤
  **마스크 영역만** 원본에 합성한다 (나머지 픽셀은 원본 그대로)
- 모델 파일이 없거나 onnxruntime 이 없으면 Telea 로 (기능은 유지)
- 영상·GIF 는 프레임이 많아(프레임당 CPU 약 1초) 기본 Telea — INPAINT_ENGINE 설정은 사진에만 적용
"""

from __future__ import annotations

import threading
from typing import Optional

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings

LAMA_SIZE = 512
CONTEXT = 0.6  # 마스크 상자 크기 대비 주변 여유 (주변 무늬를 보고 그리게)
MIN_CROP = 256  # 아주 작은 물체도 이만큼은 주변을 본다

_LOCK = threading.Lock()
_SESSION = None
_MISSING_LOGGED = False
_FAILED: tuple[str, float] | None = None  # 로드에 실패한 (경로, 수정 시각) — 같은 파일로 매 요청 다시 시도하지 않게


def _session(settings: Settings):
    """LaMa 세션 (프로세스당 한 번 로드). 없으면 None.

    파일이 없다가 나중에 생기면(기동 시 자동 받기 — services/model_fetch) 그때 로드한다.
    """
    global _SESSION, _MISSING_LOGGED, _FAILED
    with _LOCK:
        if _SESSION is not None:
            return _SESSION
        path = settings.inpaint_model_file
        if not path.is_file():
            if not _MISSING_LOGGED:
                logger.info("LaMa 모델 없음 — 대상 지우기는 Telea 로 (생기면 바로 LaMa): {}", path)
                _MISSING_LOGGED = True
            return None
        stamp = (str(path), path.stat().st_mtime)
        if _FAILED == stamp:
            return None
        from app.utils.onnx_utils import create_session

        _SESSION = create_session(path, None)
        if _SESSION is not None:
            logger.info("LaMa 인페인팅 모델 로드: {}", path.name)
        else:
            _FAILED = stamp
        return _SESSION


def lama_available(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return settings.inpaint_engine != "telea" and _session(settings) is not None


def _crop_box(mask: np.ndarray) -> tuple[int, int, int, int]:
    """마스크 상자 + 주변 여유 (정사각형에 가깝게, 이미지 안으로 자름)."""
    ys, xs = np.nonzero(mask)
    h, w = mask.shape[:2]
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    side = max(x1 - x0, y1 - y0)
    side = int(max(MIN_CROP, side * (1 + 2 * CONTEXT)))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    left = int(np.clip(cx - side // 2, 0, max(0, w - side)))
    top = int(np.clip(cy - side // 2, 0, max(0, h - side)))
    return left, top, min(w, left + side), min(h, top + side)


def lama_inpaint(image: np.ndarray, mask: np.ndarray, settings: Settings | None = None) -> Optional[np.ndarray]:
    """BGR 이미지 + 0/255 마스크 → 메운 BGR. 모델이 없거나 실패하면 None (호출 측이 Telea 로)."""
    settings = settings or get_settings()
    session = _session(settings)
    if session is None or not mask.any():
        return None
    try:
        left, top, right, bottom = _crop_box(mask)
        crop = image[top:bottom, left:right]
        crop_m = mask[top:bottom, left:right]
        ch, cw = crop.shape[:2]
        rgb = cv2.cvtColor(cv2.resize(crop, (LAMA_SIZE, LAMA_SIZE), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        m = cv2.resize(crop_m, (LAMA_SIZE, LAMA_SIZE), interpolation=cv2.INTER_NEAREST)
        img_in = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        mask_in = (m > 127).astype(np.float32)[None, None]
        inputs = session.get_inputs()
        out = session.run(None, {inputs[0].name: img_in, inputs[1].name: mask_in})[0][0]
        out = out.transpose(1, 2, 0)  # 이 모델(lama_fp32.onnx)은 입력 0~1, 출력 0~255
        filled = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        filled = cv2.resize(filled, (cw, ch), interpolation=cv2.INTER_CUBIC)
        result = image.copy()
        region = result[top:bottom, left:right]
        hole = crop_m > 127
        region[hole] = filled[hole]
        return result
    except Exception:
        logger.exception("LaMa 인페인팅 실패 — Telea 로 대신")
        return None
