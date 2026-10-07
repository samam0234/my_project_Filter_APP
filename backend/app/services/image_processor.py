"""
OpenCV 전처리 + 공용 세그멘터 보관 (LangGraph 노드가 사용).

흐름은 workflows/graph.run_pipeline 이 담당한다 — 단일·배치·재시도 모두 같은 그래프를 탄다.
여기에는 전처리(CLAHE)와 세그멘터 싱글톤만 남긴다. 예전 run()/process_batch_generator 는
인스턴스 선택(selector)·원본 크기 복원·재시도를 건너뛰어 결과가 달라지므로 삭제했다.

주의:
  - 원본은 보존하고, 각 단계는 복사본에서 작업하는 것이 원칙
  - 세그멘테이션 본체는 Segmentor 에 위임
"""

from __future__ import annotations

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.services.segmentation import Segmentor
from app.utils.image_utils import resize_keep_aspect


class ImageProcessor:
    """LangGraph 노드가 공유하는 전처리기 + 세그멘터 (nodes._get_processor 싱글톤)."""

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
