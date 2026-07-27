"""Segmentation backends. Phase 1: YOLO-seg (ONNX / Ultralytics). Phase 2: DINO+SAM2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.utils.onnx_utils import create_session


@dataclass
class SegmentationResult:
    mask: np.ndarray
    confidences: List[float] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    backend: str = "stub"


class Segmentor:
    """Phase-gated segmentor. Phase 1 uses YOLO; Phase 2 can swap backends."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session = None
        self._yolo = None
        self._ready = False
        self._init_backend()

    def _init_backend(self) -> None:
        model_path = self.settings.yolo_model_file
        # Prefer Ultralytics if .pt or package available; else ONNX session
        if model_path.suffix.lower() in {".pt", ".onnx"} and model_path.exists():
            try:
                from ultralytics import YOLO

                self._yolo = YOLO(str(model_path))
                self._ready = True
                logger.info("YOLO segmentor ready: {}", model_path)
                return
            except Exception as exc:
                logger.warning("Ultralytics load failed: {}", exc)

        self._session = create_session(model_path)
        self._ready = self._session is not None
        if not self._ready:
            logger.warning(
                "No segmentation model loaded. Using center-prior stub mask. "
                "Place weights at: {}",
                model_path,
            )

    @property
    def ready(self) -> bool:
        return self._ready

    def predict(
        self,
        image: np.ndarray,
        targets: Optional[List[str]] = None,
    ) -> SegmentationResult:
        """Return instance-union mask for requested targets."""
        targets = targets or ["person"]
        if self._yolo is not None:
            return self._predict_yolo(image, targets)
        # Stub: elliptical prior so pipeline is testable without weights
        return self._stub_mask(image, targets)

    def _predict_yolo(
        self,
        image: np.ndarray,
        targets: List[str],
    ) -> SegmentationResult:
        img = image.copy()
        results = self._yolo.predict(img, verbose=False)
        h, w = img.shape[:2]
        union = np.zeros((h, w), dtype=np.uint8)
        confidences: List[float] = []
        labels: List[str] = []

        target_set = {t.lower() for t in targets}
        for r in results:
            names = r.names or {}
            if r.masks is None:
                continue
            masks = r.masks.data.cpu().numpy()
            boxes = r.boxes
            for i, m in enumerate(masks):
                cls_id = int(boxes.cls[i].item()) if boxes is not None else -1
                conf = float(boxes.conf[i].item()) if boxes is not None else 0.0
                label = str(names.get(cls_id, cls_id)).lower()
                if target_set and label not in target_set and "all" not in target_set:
                    # if targets are free-form, keep high-conf detections as fallback
                    if conf < self.settings.min_confidence:
                        continue
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
                binary = (m_resized > 0.5).astype(np.uint8) * 255
                union = cv2.bitwise_or(union, binary)
                confidences.append(conf)
                labels.append(label)

        if not union.any():
            return self._stub_mask(image, targets)

        return SegmentationResult(
            mask=union,
            confidences=confidences,
            labels=labels,
            backend="yolo",
        )

    def _stub_mask(
        self,
        image: np.ndarray,
        targets: List[str],
    ) -> SegmentationResult:
        """Deterministic placeholder mask (center ellipse) for scaffold/demo."""
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (max(1, w // 4), max(1, h // 3))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        logger.debug("Using stub segmentation mask for targets={}", targets)
        return SegmentationResult(
            mask=mask,
            confidences=[0.5],
            labels=targets,
            backend="stub",
        )


# Phase 2 placeholder
def predict_grounding_sam2(
    image: np.ndarray,
    prompt: str,
) -> SegmentationResult:
    """Phase 2: Grounding DINO + SAM2. Not implemented in Phase 1."""
    raise NotImplementedError("Grounding DINO + SAM2 is Phase 2.")
