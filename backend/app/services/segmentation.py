"""세그멘테이션 백엔드. Phase 1: YOLO-seg (ONNX/Ultralytics). Phase 2: DINO+SAM2."""

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
    """세그 추론 결과.

    mask: 0/255 단일 채널 합집합 마스크
    confidences / labels: 인스턴스별 메타
    backend: "yolo" | "stub" 등 어떤 경로로 만들었는지
    """

    mask: np.ndarray
    confidences: List[float] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    backend: str = "stub"


class Segmentor:
    """Phase 게이트 세그멘터. Phase 1은 YOLO, Phase 2에서 백엔드 교체 가능."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session = None  # ONNX 세션 (선택)
        self._yolo = None  # Ultralytics YOLO 객체 (선택)
        self._ready = False
        self._init_backend()

    def _init_backend(self) -> None:
        """설정 경로의 가중치를 로드. 없으면 stub 모드로 둔다."""
        model_path = self.settings.yolo_model_file
        # .pt/패키지 있으면 Ultralytics, 아니면 ONNX 세션 시도
        if model_path.suffix.lower() in {".pt", ".onnx"} and model_path.exists():
            try:
                from ultralytics import YOLO

                self._yolo = YOLO(str(model_path))
                self._ready = True
                logger.info("YOLO 세그멘터 준비: {}", model_path)
                return
            except Exception as exc:
                logger.warning("Ultralytics 로드 실패: {}", exc)

        # Ultralytics 실패 시 onnxruntime 세션 (추가 추론 로직은 확장 지점)
        self._session = create_session(model_path)
        self._ready = self._session is not None
        if not self._ready:
            logger.warning(
                "세그 모델 없음. 중앙 stub 마스크 사용. "
                "가중치 경로: {}",
                model_path,
            )

    @property
    def ready(self) -> bool:
        """모델이 실제로 로드되었는지."""
        return self._ready

    def predict(
        self,
        image: np.ndarray,
        targets: Optional[List[str]] = None,
    ) -> SegmentationResult:
        """요청 대상에 대한 인스턴스 마스크 합집합 반환."""
        targets = targets or ["person"]
        if self._yolo is not None:
            return self._predict_yolo(image, targets)
        # 가중치 없을 때: 파이프라인 e2e 검증용 타원 stub
        return self._stub_mask(image, targets)

    def _predict_yolo(
        self,
        image: np.ndarray,
        targets: List[str],
    ) -> SegmentationResult:
        """Ultralytics predict → 클래스 필터 → 마스크 bitwise OR 합치기."""
        img = image.copy()
        results = self._yolo.predict(img, verbose=False)
        h, w = img.shape[:2]
        # 여러 인스턴스 마스크를 한 장으로 합침
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
                # target 목록에 없으면 confidence 낮을 때 스킵
                if target_set and label not in target_set and "all" not in target_set:
                    # 자유 형식 target이면 고신뢰 탐지를 fallback으로 유지
                    if conf < self.settings.min_confidence:
                        continue
                # 마스크 해상도를 원본 크기에 맞춤
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
                binary = (m_resized > 0.5).astype(np.uint8) * 255
                union = cv2.bitwise_or(union, binary)
                confidences.append(conf)
                labels.append(label)

        # 유효 마스크가 하나도 없으면 stub 로 대체
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
        """스캐폴드/데모용 중앙 타원 stub 마스크.

        모델 없이도 upload → 효과 파이프라인을 돌려 보기 위함.
        """
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (max(1, w // 4), max(1, h // 3))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        logger.debug("stub 세그 마스크 사용 targets={}", targets)
        return SegmentationResult(
            mask=mask,
            confidences=[0.5],
            labels=targets,
            backend="stub",
        )


# Phase 2 자리 표시 (Grounding DINO + SAM2)
def predict_grounding_sam2(
    image: np.ndarray,
    prompt: str,
) -> SegmentationResult:
    """Phase 2: Grounding DINO + SAM2. Phase 1 미구현."""
    raise NotImplementedError("Grounding DINO + SAM2 is Phase 2.")
