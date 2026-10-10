"""배경 덩어리(건물·하늘·도로·나무·잔디·물…) 의미 분할 — SegFormer(ADE20K 150클래스) ONNX.

YOLO(COCO 80클래스)는 "사람·자동차" 같은 낱개 물체만 알고 건물·하늘 같은 덩어리는 모른다. 이 모듈이 그 대상을 맡는다.
  - torch·transformers 없이 onnxruntime 만으로 돈다 (Docker 슬림 이미지에서도 사용 가능)
  - 사용자가 말하는 단위로 묶는다: "건물" = building + house + skyscraper + hovel (prompt_spec.STUFF_GROUPS)
  - 묶음 확률 = 소속 클래스 확률의 합 (저해상도에서 softmax → 합 → 이미지 크기로 선형 확대 → 임계)
    → 클래스 하나하나가 아니라 묶음이 이기는 픽셀을 잡아 "건물인지 집인지"로 갈리는 구멍이 안 생긴다
  - 연결된 덩어리마다 인스턴스로 내보내 위치·크기 선택("왼쪽 건물", "가장 큰 건물")이 그대로 동작한다

모델 파일은 scripts/export_stuff_onnx.py 로 만든다 (backend/models/segformer-ade.onnx + .labels.json).
없으면 이 경로는 꺼지고 기존 YOLO 흐름이 그대로 간다.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.services.prompt_spec import STUFF_GROUPS  # noqa: F401  (실험·테스트가 여기서 가져다 쓴다)

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
MIN_COMPONENT_RATIO = 0.003  # 이미지 면적 대비 이보다 작은 조각은 인스턴스로 내지 않는다 (마스크에는 남는다)
MAX_COMPONENTS = 24


def preprocess(rgb: np.ndarray, size: int) -> np.ndarray:
    """RGB uint8 (H, W, 3) → 정규화한 float32 (1, 3, size, size). HF 이미지 프로세서와 같다 (정사각형으로 리사이즈)."""
    resized = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)
    x = (resized.astype(np.float32) / 255.0 - MEAN) / STD
    return np.ascontiguousarray(x.transpose(2, 0, 1)[None])


def group_ids(id2label: Dict[int, str], group: str) -> List[int]:
    """묶음 이름 → 모델 클래스 번호 목록 (라벨은 공백 정리해서 비교)."""
    wanted = set(STUFF_GROUPS[group])
    return sorted(i for i, name in id2label.items() if name.strip().lower() in wanted)


def _softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=0, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=0, keepdims=True)


def group_probability(logits: np.ndarray, ids: Sequence[int], out_hw: Tuple[int, int]) -> np.ndarray:
    """logits (C, h, w) → 묶음 확률지도 (H, W) float32 0~1."""
    prob = _softmax(logits)[list(ids)].sum(axis=0)
    h, w = out_hw
    return cv2.resize(prob.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)


def split_components(mask: np.ndarray, prob: np.ndarray, label: str):
    """0/255 마스크를 연결 성분으로 나눠 (mask, label, confidence, bbox) 목록으로. 큰 순, 최대 MAX_COMPONENTS."""
    h, w = mask.shape[:2]
    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), connectivity=8)
    order = sorted(range(1, n), key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    out = []
    for i in order[:MAX_COMPONENTS]:
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < MIN_COMPONENT_RATIO * h * w:
            break
        comp = np.where(labels == i, 255, 0).astype(np.uint8)
        x, y = int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP])
        bw, bh = int(stats[i, cv2.CC_STAT_WIDTH]), int(stats[i, cv2.CC_STAT_HEIGHT])
        out.append((comp, label, float(prob[labels == i].mean()), (x, y, x + bw, y + bh)))
    return out


class StuffSegmenter:
    """SegFormer ONNX 로 요청한 묶음의 마스크를 만든다. 모델 파일이 없으면 available=False."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session = None
        self._input = ""
        self._size = 512
        self._id2label: Dict[int, str] = {}
        self._lock = threading.Lock()
        path = self.settings.stuff_model_file
        if not self.settings.stuff_seg_enabled:
            return
        from app.utils.onnx_utils import create_session

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self.settings.stuff_use_gpu else None
        self._session = create_session(path, providers)
        labels = path.with_suffix(".labels.json")
        if self._session is None or not labels.is_file():
            if self._session is not None:
                logger.warning("배경 덩어리 모델은 있는데 라벨 파일이 없다: {}", labels)
            self._session = None
            return
        meta = self._session.get_inputs()[0]
        self._input = meta.name
        shape = meta.shape  # [N, 3, H, W]
        self._size = int(shape[2]) if isinstance(shape[2], int) else 512
        self._id2label = {int(k): v for k, v in json.loads(labels.read_text(encoding="utf-8")).items()}
        logger.info("배경 덩어리 세그 준비: {} 입력 {}px", path.name, self._size)

    @property
    def available(self) -> bool:
        return self._session is not None

    def group_names(self) -> List[str]:
        return list(STUFF_GROUPS) if self.available else []

    def logits(self, bgr: np.ndarray) -> np.ndarray:
        """BGR 이미지 → (C, h, w) logits."""
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        x = preprocess(rgb, self._size)
        with self._lock:  # onnxruntime 세션은 스레드 안전하지만 GPU 메모리 급증을 막으려고 직렬화
            out = self._session.run(None, {self._input: x})[0]
        return out[0]

    def predict(self, bgr: np.ndarray, groups: Sequence[str]):
        """요청 묶음들의 합집합 마스크와 인스턴스. 반환: (mask 0/255, [(mask, label, conf, bbox)...]) ."""
        h, w = bgr.shape[:2]
        logits = self.logits(bgr)
        union = np.zeros((h, w), np.uint8)
        instances = []
        thr = self.settings.stuff_min_prob
        for group in groups:
            ids = group_ids(self._id2label, group)
            if not ids:
                continue
            prob = group_probability(logits, ids, (h, w))
            mask = np.where(prob >= thr, 255, 0).astype(np.uint8)
            union = np.maximum(union, mask)
            instances.extend(split_components(mask, prob, group))
        return union, instances
