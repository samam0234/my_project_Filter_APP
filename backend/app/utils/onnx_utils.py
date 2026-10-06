"""Phase 1 YOLO-seg 추론용 ONNX Runtime 헬퍼.

Segmentor 가 Ultralytics .pt 로드에 실패했을 때
.onnx 세션 생성을 시도하는 경로에서 사용한다.

세션 생성 · 입력 이름 · YOLO-seg 전처리(letterbox)·후처리(NMS·마스크 복원)까지 제공한다
(`run_yolo_seg_onnx`). Ultralytics 없이 onnxruntime 만으로 세그가 돌아 Docker 이미지를 가볍게 할 수 있다.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from loguru import logger


def create_session(model_path: Path | str, providers: Optional[list[str]] = None) -> Any:
    """모델 파일이 있으면 onnxruntime InferenceSession 생성.

    파일이 없거나 onnxruntime 미설치 시 None (호출측이 stub 으로 폴백).
    providers 기본: CPUExecutionProvider.
    """
    # =============================================================================
    # [이미 구현된 구간 · 바이브] InferenceSession 생성
    # =============================================================================
    path = Path(model_path)
    if not path.exists():
        logger.warning("ONNX 모델 없음: {}", path)
        return None
    if path.suffix.lower() != ".onnx":
        # .pt 등은 ONNX 가 아님 — 열면 INVALID_PROTOBUF 예외로 파이프라인이 멈춘다
        logger.warning("ONNX 파일 아님 (세션 생략): {}", path)
        return None

    try:
        import onnxruntime as ort
    except ImportError as exc:
        logger.error("onnxruntime 미설치: {}", exc)
        return None

    if providers is None:
        providers = ["CPUExecutionProvider"]

    try:
        session = ort.InferenceSession(str(path), providers=providers)
    except Exception as exc:  # 손상·버전 불일치 → stub 으로 폴백
        logger.error("ONNX 모델 로드 실패: {} ({})", path, exc)
        return None
    logger.info("ONNX 모델 로드: {} providers={}", path, session.get_providers())
    return session


def session_input_name(session: Any) -> str:
    """세션 첫 번째 입력 텐서 이름 (보통 'images')."""
    # =============================================================================
    # [이미 구현된 구간 · 바이브] 입력 텐서 이름
    # =============================================================================
    return session.get_inputs()[0].name


# =============================================================================
# YOLO-seg ONNX 추론 — 전처리 · 후처리 (Ultralytics export 형식)
# -----------------------------------------------------------------------------
# 입력  images  [1, 3, S, S]  RGB · 0~1 · letterbox(회색 114 패딩)
# 출력  output0 [1, 4 + nc + nm, A]  (cx, cy, w, h | 클래스 점수 nc | 마스크 계수 nm), NMS 없음
#       output1 [1, nm, mh, mw]      마스크 원형(proto)
# 후처리는 Ultralytics 정밀 방식(retina_masks)과 같은 순서: 신뢰도 필터 → 클래스별 NMS → 계수·proto 곱
#   → proto 격자에서 letterbox 패딩 제거 → 원본 크기로 확대 → 원본 해상도에서 박스로 자름 → 로짓 > 0 (= sigmoid > 0.5)
#   (격자 해상도에서 먼저 자르면 가장자리가 거칠어 IoU 가 떨어졌다 — docs/plan/ONNX_INFERENCE.md)
# 검증: scripts/experiments/onnx_vs_pt.py (같은 이미지에서 .pt 결과와 IoU 비교)
# =============================================================================

NMS_IOU = 0.7  # Ultralytics predict 기본
MAX_DET = 300
PRE_NMS_TOPK = 1000  # NMS 전에 신뢰도 상위만 (속도)
PAD_VALUE = 114


def input_size(session: Any) -> tuple[int, int]:
    """모델 입력 (높이, 너비). 동적 축이면 640."""
    shape = session.get_inputs()[0].shape
    h, w = shape[2], shape[3]
    return (h if isinstance(h, int) else 640, w if isinstance(w, int) else 640)


def letterbox(image_bgr: np.ndarray, size: tuple[int, int]) -> tuple[np.ndarray, float, tuple[int, int]]:
    """비율 유지 축소 + 가운데 정렬 회색 패딩. 반환: (패딩된 BGR, 배율, (top, left))."""
    h, w = image_bgr.shape[:2]
    sh, sw = size
    r = min(sh / h, sw / w)
    nh, nw = round(h * r), round(w * r)
    resized = cv2.resize(image_bgr, (nw, nh), interpolation=cv2.INTER_LINEAR) if (nh, nw) != (h, w) else image_bgr
    dh, dw = (sh - nh) / 2, (sw - nw) / 2
    top, bottom = round(dh - 0.1), round(dh + 0.1)
    left, right = round(dw - 0.1), round(dw + 0.1)
    out = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(PAD_VALUE,) * 3)
    return out, r, (top, left)


def preprocess(image_bgr: np.ndarray, size: tuple[int, int]) -> tuple[np.ndarray, float, tuple[int, int]]:
    """BGR 이미지 → NCHW float32 RGB 0~1 텐서."""
    boxed, r, pad = letterbox(image_bgr, size)
    blob = np.ascontiguousarray(boxed[:, :, ::-1].transpose(2, 0, 1), dtype=np.float32)[None] / 255.0
    return blob, r, pad


def _nms(xyxy: np.ndarray, conf: np.ndarray, cls: np.ndarray, iou: float) -> list[int]:
    """클래스별 NMS (클래스 번호만큼 박스를 밀어 서로 겹치지 않게 한 뒤 한 번에)."""
    if len(conf) == 0:
        return []
    shifted = xyxy + cls[:, None].astype(np.float32) * 8192.0
    rects = [[float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])] for b in shifted]
    idx = cv2.dnn.NMSBoxes(rects, conf.astype(float).tolist(), 0.0, iou)
    return [int(i) for i in np.array(idx).reshape(-1)]


def postprocess(
    outputs: list[np.ndarray],
    orig_shape: tuple[int, int],
    r: float,
    pad: tuple[int, int],
    size: tuple[int, int],
    conf_threshold: float,
) -> list[tuple[int, float, np.ndarray]]:
    """모델 출력 → [(클래스 번호, 신뢰도, 원본 크기 0/255 마스크), ...] (신뢰도 높은 순)."""
    pred = np.asarray(outputs[0])[0].T  # (A, 4+nc+nm)
    proto = np.asarray(outputs[1])[0]  # (nm, mh, mw)
    nm, mh, mw = proto.shape
    nc = pred.shape[1] - 4 - nm
    scores = pred[:, 4 : 4 + nc]
    cls = scores.argmax(1)
    conf = scores[np.arange(len(scores)), cls]
    keep = np.nonzero(conf >= conf_threshold)[0]
    if len(keep) == 0:
        return []
    if len(keep) > PRE_NMS_TOPK:
        keep = keep[np.argsort(-conf[keep])[:PRE_NMS_TOPK]]
    box, conf, cls, coef = pred[keep, :4], conf[keep], cls[keep], pred[keep, 4 + nc :]
    xyxy = np.stack([box[:, 0] - box[:, 2] / 2, box[:, 1] - box[:, 3] / 2,
                     box[:, 0] + box[:, 2] / 2, box[:, 1] + box[:, 3] / 2], axis=1)
    picked = _nms(xyxy, conf, cls, NMS_IOU)[:MAX_DET]
    if not picked:
        return []

    sh, sw = size
    h, w = orig_shape
    top, left = pad
    # proto 격자에서 letterbox 패딩 제거 범위 (Ultralytics scale_masks 와 같은 반올림)
    pad_h, pad_w = (mh - h * min(mh / h, mw / w)) / 2, (mw - w * min(mh / h, mw / w)) / 2
    t, l = round(pad_h - 0.1), round(pad_w - 0.1)
    b_, r_ = mh - round(pad_h + 0.1), mw - round(pad_w + 0.1)
    logits = (coef[picked] @ proto.reshape(nm, -1)).reshape(-1, mh, mw)
    xs = np.arange(w, dtype=np.float32)[None, :]
    ys = np.arange(h, dtype=np.float32)[:, None]
    results: list[tuple[int, float, np.ndarray]] = []
    for k, i in enumerate(picked):
        # 정밀 방식(Ultralytics retina_masks): 패딩 제거 → 원본 크기로 확대 → 그 해상도에서 박스로 자름
        full = cv2.resize(logits[k][t:b_, l:r_], (w, h), interpolation=cv2.INTER_LINEAR)
        x1, y1, x2, y2 = (xyxy[i] - np.array([left, top, left, top], dtype=np.float32)) / r
        x1, x2 = np.clip([x1, x2], 0, w)
        y1, y2 = np.clip([y1, y2], 0, h)
        inside = (xs >= x1) & (xs < x2) & (ys >= y1) & (ys < y2)
        results.append((int(cls[i]), float(conf[i]), ((full > 0) & inside).astype(np.uint8) * 255))
    return results


def class_names(session: Any) -> dict[int, str]:
    """ONNX 메타데이터의 클래스 이름 (Ultralytics export 가 `names` 에 dict 문자열로 기록). 없으면 빈 dict."""
    try:
        raw = session.get_modelmeta().custom_metadata_map.get("names")
        parsed = ast.literal_eval(raw) if raw else {}
        return {int(k): str(v) for k, v in parsed.items()}
    except Exception as exc:  # 메타데이터가 깨져도 추론은 가능 — 이름만 숫자로
        logger.warning("ONNX 클래스 이름 읽기 실패: {}", exc)
        return {}


def run_yolo_seg_onnx(
    session: Any, image_bgr: np.ndarray, conf_threshold: float = 0.25
) -> list[tuple[int, float, np.ndarray]]:
    """BGR 이미지 한 장 → [(클래스 번호, 신뢰도, 원본 크기 0/255 마스크), ...]."""
    size = input_size(session)
    blob, r, pad = preprocess(image_bgr, size)
    outputs = session.run(None, {session_input_name(session): blob})
    return postprocess(outputs, image_bgr.shape[:2], r, pad, size, conf_threshold)
