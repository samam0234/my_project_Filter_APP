"""
OpenCV pipeline facade (steps 3 & 5 of the 7-step flow).

Steps:
  preprocess → (segmentation external) → refine/effects
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.models.request import ParsedPrompt
from app.services.effects import apply_effects, refine_mask
from app.services.segmentation import SegmentationResult, Segmentor
from app.services.validator import ValidationResult, score_mask
from app.utils.image_utils import decode_image_bytes, resize_keep_aspect


@dataclass
class PipelineOutput:
    original: np.ndarray
    preprocessed: np.ndarray
    mask: np.ndarray
    result: np.ndarray
    seg: SegmentationResult
    validation: ValidationResult
    parsed: ParsedPrompt


class ImageProcessor:
    """Synchronous single-image processing entry used by LangGraph nodes / API."""

    def __init__(
        self,
        settings: Settings | None = None,
        segmentor: Segmentor | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.segmentor = segmentor or Segmentor(self.settings)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Resize + CLAHE on L channel. Always copy."""
        img, _ = resize_keep_aspect(image.copy(), self.settings.max_image_side)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(
            clipLimit=self.settings.clahe_clip_limit,
            tileGridSize=(
                self.settings.clahe_tile_size,
                self.settings.clahe_tile_size,
            ),
        )
        l2 = clahe.apply(l)
        merged = cv2.merge([l2, a, b])
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    def run(
        self,
        image_bytes: bytes,
        parsed: ParsedPrompt,
    ) -> PipelineOutput:
        original = decode_image_bytes(image_bytes)
        preprocessed = self.preprocess(original)

        seg = self.segmentor.predict(preprocessed, targets=parsed.target)
        validation = score_mask(seg.mask, seg.confidences, self.settings)

        # On fallback/failed, still attempt a best-effort effect for demo UX
        mask_for_fx = refine_mask(seg.mask, preprocessed)
        if validation.ok:
            result = apply_effects(original, mask_for_fx, parsed)
        else:
            logger.warning("Validation: {} — applying best-effort effects", validation.message)
            result = apply_effects(original, mask_for_fx, parsed)

        return PipelineOutput(
            original=original,
            preprocessed=preprocessed,
            mask=mask_for_fx,
            result=result,
            seg=seg,
            validation=validation,
            parsed=parsed,
        )

    def process_batch_generator(
        self,
        items: List[Tuple[bytes, ParsedPrompt]],
    ):
        """Phase 2 helper: yield results one-by-one (memory-safe)."""
        for image_bytes, parsed in items:
            yield self.run(image_bytes, parsed)
