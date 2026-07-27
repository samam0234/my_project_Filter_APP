"""Mask quality validation and fallback decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from app.core.config import Settings, get_settings
from app.core.constants import JobStatus


@dataclass
class ValidationResult:
    ok: bool
    status: str
    quality_score: float
    message: str = ""


def mask_area_ratio(mask: np.ndarray) -> float:
    m = mask
    if m.ndim == 3:
        m = m[:, :, 0]
    total = m.size
    if total == 0:
        return 0.0
    return float(np.count_nonzero(m > 0)) / float(total)


def score_mask(
    mask: np.ndarray,
    confidences: List[float] | None,
    settings: Settings | None = None,
) -> ValidationResult:
    settings = settings or get_settings()
    confidences = confidences or []

    ratio = mask_area_ratio(mask)
    mean_conf = float(np.mean(confidences)) if confidences else 0.0

    # quality: blend area fitness + confidence
    area_score = 1.0 - abs(ratio - 0.35) / 0.65  # prefer mid-sized subjects
    area_score = max(0.0, min(1.0, area_score))
    quality = 0.5 * area_score + 0.5 * min(1.0, mean_conf / max(settings.min_confidence, 1e-6))
    quality = float(max(0.0, min(1.0, quality)))

    if ratio <= 0.0:
        return ValidationResult(
            ok=False,
            status=JobStatus.FAILED.value,
            quality_score=0.0,
            message="Empty mask.",
        )
    if ratio < settings.mask_min_area_ratio:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"Mask area too small ({ratio:.4f}).",
        )
    if ratio > settings.mask_max_area_ratio:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"Mask area too large ({ratio:.4f}).",
        )
    if confidences and mean_conf < settings.min_confidence:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"Confidence too low ({mean_conf:.3f}).",
        )

    return ValidationResult(
        ok=True,
        status=JobStatus.OK.value,
        quality_score=quality,
        message="ok",
    )
