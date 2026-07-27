"""마스크 품질 검증 및 fallback 판단."""

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

    # 품질: 면적 적합도 + confidence 혼합
    area_score = 1.0 - abs(ratio - 0.35) / 0.65  # 중간 크기 피사체 선호
    area_score = max(0.0, min(1.0, area_score))
    quality = 0.5 * area_score + 0.5 * min(1.0, mean_conf / max(settings.min_confidence, 1e-6))
    quality = float(max(0.0, min(1.0, quality)))

    if ratio <= 0.0:
        return ValidationResult(
            ok=False,
            status=JobStatus.FAILED.value,
            quality_score=0.0,
            message="빈 마스크.",
        )
    if ratio < settings.mask_min_area_ratio:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"마스크 면적 너무 작음 ({ratio:.4f}).",
        )
    if ratio > settings.mask_max_area_ratio:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"마스크 면적 너무 큼 ({ratio:.4f}).",
        )
    if confidences and mean_conf < settings.min_confidence:
        return ValidationResult(
            ok=False,
            status=JobStatus.FALLBACK.value,
            quality_score=quality,
            message=f"confidence 너무 낮음 ({mean_conf:.3f}).",
        )

    return ValidationResult(
        ok=True,
        status=JobStatus.OK.value,
        quality_score=quality,
        message="ok",
    )
