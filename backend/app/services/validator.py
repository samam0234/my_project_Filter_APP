"""마스크 품질 검증 및 fallback 판단.

세그 결과 마스크가 “쓸 만한지” 점수화하고,
ok / fallback / failed 상태 문자열을 결정한다.

임계값은 Settings:
  - mask_min_area_ratio / mask_max_area_ratio
  - min_confidence
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from app.core.config import Settings, get_settings
from app.core.constants import JobStatus


@dataclass
class ValidationResult:
    """검증 한 건의 결과 묶음."""

    ok: bool  # True 이면 effect 로 직행
    status: str  # JobStatus 값 문자열
    quality_score: float  # 0.0~1.0
    message: str = ""  # 사람이 읽는 사유


def mask_area_ratio(mask: np.ndarray) -> float:
    """마스크가 이미지에서 차지하는 면적 비율 (0.0~1.0)."""
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
    """면적 비율 + confidence 로 품질을 평가한다.

    판정 우선순위:
      1) 완전 빈 마스크 → failed
      2) 면적 너무 작음/큼 → fallback
      3) 평균 confidence 미달 → fallback
      4) 그 외 → ok

    quality_score 는 면적 적합도(중간 크기 선호)와 confidence 의 평균.
    """
    settings = settings or get_settings()
    confidences = confidences or []

    ratio = mask_area_ratio(mask)
    mean_conf = float(np.mean(confidences)) if confidences else 0.0

    # -------------------------------------------------------------------------
    # 【수동·튜닝】 품질 점수 공식 (하드코딩 상수)
    # 조건: 0.35 = “이상적 피사체 면적 비율”, 0.5/0.5 = 면적·conf 가중치
    # 기능: quality_score 0~1 산출 + ok/fallback/failed 판정 재료
    # 임계 자체(min/max area, min_confidence)는 Settings 에 있음
    # -------------------------------------------------------------------------
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
