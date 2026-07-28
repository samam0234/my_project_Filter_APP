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
        # ---------------------------------------------------------------------
        # 【수동·파일 배치 필수】 가중치 경로 = Settings.yolo_model_path
        # 조건:
        #   - 파일이 존재하고 확장자가 .pt 또는 .onnx
        #   - 서비스 본선: **instance segmentation** 모델 (yolo26s-seg)
        #   - detect 전용(yolo26s.pt) 을 여기 넣으면 masks 가 없어 stub 로 떨어질 수 있음
        # 해야 할 일 (코드 밖):
        #   1) models/yolo26s-seg.pt 다운로드 또는 학습 best.pt 복사
        #   2) .env YOLO_MODEL_PATH 확인
        #   3) 로컬은 requirements.txt(ultralytics), Docker 는 onnx 또는 풀 스택
        # ---------------------------------------------------------------------
        model_path = self.settings.yolo_model_file
        # .pt 있으면 Ultralytics, 아니면 ONNX 세션 시도
        if model_path.suffix.lower() in {".pt", ".onnx"} and model_path.exists():
            try:
                from ultralytics import YOLO

                self._yolo = YOLO(str(model_path))
                self._ready = True
                logger.info("YOLO 세그멘터 준비: {}", model_path)
                return
            except Exception as exc:
                logger.warning("Ultralytics 로드 실패: {}", exc)

        # 【수동·확장】 ONNX 추론 루프 미완 — 세션만 생성, 실제 전후처리는 추후 구현
        # 조건: .onnx 파일 + onnxruntime 설치, Ultralytics 실패/미사용 시
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
        # 【수동】 기본 target — prompt 분석 실패/누락 시 이 클래스만 시도
        # 학습 names 와 동일한 소문자 라벨을 쓸 것
        targets = targets or ["person"]
        if self._yolo is not None:
            return self._predict_yolo(image, targets)
        # 【수동 아님·동작 설명】 가중치 없을 때 stub — 중앙 타원 가짜 마스크
        # 조건: 모델 파일 없음 / 로드 실패. 기능: e2e 파이프라인만 통과시킴
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
            # 【수동·주의】 masks 가 None 이면 detect 전용 모델일 수 있음 → seg 가중치 사용
            if r.masks is None:
                continue
            masks = r.masks.data.cpu().numpy()
            boxes = r.boxes
            for i, m in enumerate(masks):
                cls_id = int(boxes.cls[i].item()) if boxes is not None else -1
                conf = float(boxes.conf[i].item()) if boxes is not None else 0.0
                label = str(names.get(cls_id, cls_id)).lower()
                # 【수동·정책】 target 필터 규칙
                # 조건: label 이 target 목록에 없고 "all" 도 아니면
                #   conf < min_confidence 인 인스턴스는 버림
                #   conf 높으면 유지 (자유 형식 프롬프트 완화)
                # 기능: 남길 객체만 마스크 합집합. 엄격 매칭 원하면 conf 분기 제거하고 continue
                if target_set and label not in target_set and "all" not in target_set:
                    if conf < self.settings.min_confidence:
                        continue
                # 마스크 해상도를 원본 크기에 맞춤
                # 【수동·튜닝】 0.5 이진화 임계 — soft mask 품질에 따라 조정 가능
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
                binary = (m_resized > 0.5).astype(np.uint8) * 255
                union = cv2.bitwise_or(union, binary)
                confidences.append(conf)
                labels.append(label)

        # 유효 마스크가 하나도 없으면 stub 로 대체
        # 【수동·정책】 실패 시 stub 대신 빈 마스크/에러로 바꿀지 여기서 결정
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


# -----------------------------------------------------------------------------
# 【수동·Phase2 구현】 Grounding DINO + SAM2
# 조건: Phase 1 YOLO 가 완전히 동작한 뒤에만 도입 (LOGIC_STRUCTURE 규칙)
# 해야 할 기능:
#   - 텍스트 오픈보캐브 대상 탐지(DINO) → SAM2 로 정밀 마스크
#   - Segmentor.predict 백엔드 분기 또는 교체
#   - 가중치 경로·의존성을 training/requirements 와 분리
# -----------------------------------------------------------------------------
def predict_grounding_sam2(
    image: np.ndarray,
    prompt: str,
) -> SegmentationResult:
    """Phase 2: Grounding DINO + SAM2. Phase 1 미구현."""
    raise NotImplementedError("Grounding DINO + SAM2 is Phase 2.")
