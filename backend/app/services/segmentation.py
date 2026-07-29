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

        # =============================================================================
        # [이미 구현된 구간 · 바이브] Ultralytics .pt 로드
        # -----------------------------------------------------------------------------
        # 가중치 파일 배치(.env YOLO_MODEL_PATH)는 코드 밖 작업.
        # 서비스 본선: instance segmentation (yolo26s-seg). detect 전용 .pt 금지.
        # =============================================================================
        if model_path.suffix.lower() in {".pt", ".onnx"} and model_path.exists():
            try:
                from ultralytics import YOLO

                self._yolo = YOLO(str(model_path))
                self._ready = True
                logger.info("YOLO 세그멘터 준비: {}", model_path)
                return
            except Exception as exc:
                logger.warning("Ultralytics 로드 실패: {}", exc)

        # =============================================================================
        # [하드코딩 파트] ONNX 세션 준비 후 추론 연결
        # -----------------------------------------------------------------------------
        # [임무] .pt 실패/미사용 시 .onnx 로 세그 가능 (Docker 경량 축)
        # [연결] create_session → self._session / predict 의 ONNX 분기 / onnx_utils
        # [규칙] 세션만 만들고 predict 미연결이면 stub. 실패 시 _stub_mask.
        # [힌트] self._session = create_session(...); # + _predict_onnx 작성
        # =============================================================================
        # >>> 여기에 ONNX 준비·확장 작성 (아래 create_session 은 최소 바이브 유지) <<<
        #

        # =============================================================================
        # [이미 구현된 구간 · 바이브] ONNX 세션 생성 시도 + 미준비 경고
        # =============================================================================
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

        # =============================================================================
        # [이미 구현된 구간 · 바이브] YOLO .pt 경로 우선
        # =============================================================================
        if self._yolo is not None:
            return self._predict_yolo(image, targets)

        # =============================================================================
        # [하드코딩 파트] ONNX predict 분기
        # -----------------------------------------------------------------------------
        # [임무] self._session 있을 때 YOLO-seg ONNX 결과 반환
        # [연결] self._session, _stub_mask, (작성) _predict_onnx, onnx_utils
        # [규칙] 반환=SegmentationResult, backend="onnx", target 필터는 yolo 와 동일 권장
        # [힌트] if self._session is not None: return self._predict_onnx(image, targets)
        # =============================================================================
        # >>> 여기에 ONNX 분기 작성 <<<
        # if self._session is not None:
        #     return self._predict_onnx(image, targets)

        # =============================================================================
        # [이미 구현된 구간 · 바이브] 모델 없을 때 stub 마스크
        # =============================================================================
        return self._stub_mask(image, targets)

    def _predict_yolo(
        self,
        image: np.ndarray,
        targets: List[str],
    ) -> SegmentationResult:
        """Ultralytics predict → 클래스 필터 → 마스크 bitwise OR 합치기."""
        # =============================================================================
        # [이미 구현된 구간 · 바이브] _predict_yolo 본문
        # -----------------------------------------------------------------------------
        # 하드코딩 숙제 아님. 튜닝( conf 필터, 0.5 임계 )만 필요 시 수정.
        # =============================================================================
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
        """스캐폴드/데모용 중앙 타원 stub 마스크.

        모델 없이도 upload → 효과 파이프라인을 돌려 보기 위함.
        """
        # =============================================================================
        # [이미 구현된 구간 · 바이브] stub 타원 마스크
        # =============================================================================
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


# =============================================================================
# [하드코딩 파트] Grounding DINO + SAM2 백엔드
# -----------------------------------------------------------------------------
# [임무] Phase2 오픈보캐브 세그 (텍스트 → 정밀 마스크)
# [연결] Segmentor.predict 분기 후보, SegmentationResult, training 의존성 분리
# [규칙] Phase1 YOLO 안정 후. DINO 박스 → SAM2. 절대경로 금지.
# [힌트] boxes=dino...; masks=sam2...; return SegmentationResult(..., backend="dino_sam2")
# =============================================================================
def predict_grounding_sam2(
    image: np.ndarray,
    prompt: str,
) -> SegmentationResult:
    """Phase 2: Grounding DINO + SAM2. 하드코딩 구간 — 본문 직접 구현."""
    # >>> 여기에 구현 <<<
    raise NotImplementedError("Grounding DINO + SAM2 is Phase 2.")
