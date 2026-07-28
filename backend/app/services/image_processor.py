"""
OpenCV 파이프라인 파사드 (7단계 중 3·5단계).

흐름:
  전처리 → (외부 세그멘테이션) → 정제/효과

주의:
  - 원본은 보존하고, 각 단계는 복사본에서 작업하는 것이 원칙
  - 세그멘테이션 본체는 Segmentor 에 위임
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.schemas.request import ParsedPrompt
from app.services.effects import apply_effects, refine_mask
from app.services.segmentation import SegmentationResult, Segmentor
from app.services.validator import ValidationResult, score_mask
from app.utils.image_utils import decode_image_bytes, resize_keep_aspect


@dataclass
class PipelineOutput:
    """단일 이미지 처리 결과 묶음 (중간·최종 산출물)."""

    original: np.ndarray  # 원본 BGR
    preprocessed: np.ndarray  # CLAHE 등 전처리 후
    mask: np.ndarray  # 정제된 마스크
    result: np.ndarray  # 효과 적용 후 결과 이미지
    seg: SegmentationResult  # 세그 메타(confidence, labels, backend)
    validation: ValidationResult  # 마스크 품질 판정
    parsed: ParsedPrompt  # 구조화된 프롬프트


class ImageProcessor:
    """LangGraph 노드/API에서 쓰는 단일 이미지 동기 처리 진입점."""

    def __init__(
        self,
        settings: Settings | None = None,
        segmentor: Segmentor | None = None,
    ) -> None:
        # 설정·세그멘터 주입 가능 (테스트/교체 용이)
        self.settings = settings or get_settings()
        self.segmentor = segmentor or Segmentor(self.settings)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """리사이즈 + L채널 CLAHE. 항상 복사본 사용.

        CLAHE: 대비를 국소적으로 올려 세그가 경계에 유리하게 함.
        """
        # 긴 변 제한으로 메모리·속도 관리
        img, _ = resize_keep_aspect(image.copy(), self.settings.max_image_side)
        # LAB 에서 L(밝기)만 대비 향상
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
        """바이트 이미지 + 구조화 프롬프트 → 전체 처리 결과.

        1) 디코드  2) 전처리  3) 세그  4) 품질 검증  5) 마스크 정제·효과
        """
        original = decode_image_bytes(image_bytes)
        preprocessed = self.preprocess(original)

        # parsed.target 에 맞춰 마스크 생성 (YOLO 또는 stub)
        seg = self.segmentor.predict(preprocessed, targets=parsed.target)
        validation = score_mask(seg.mask, seg.confidences, self.settings)

        # 검증 실패여도 데모 UX 를 위해 효과는 best-effort 적용
        mask_for_fx = refine_mask(seg.mask, preprocessed)
        if validation.ok:
            result = apply_effects(original, mask_for_fx, parsed)
        else:
            logger.warning("검증: {} — best-effort 효과 적용", validation.message)
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
        """Phase 2용: 한 장씩 yield 하여 메모리 폭증 방지."""
        for image_bytes, parsed in items:
            yield self.run(image_bytes, parsed)
