"""ORM: 학습 데이터 카탈로그 (학습 DB).

학습에 쓸 수 있는 데이터 한 건 = 1행. 이미지·마스크 자체가 아니라 **파일 경로와 라벨**을 기록한다.

kind
  - prompt  : 문장 → ParsedPrompt 정답 (LoRA·RAG 용). answer 에 정답 JSON
  - segment : 세그 실패 이미지 (YOLO 재학습 후보). image_path 에 원본 경로
source
  - correction       : 사용자가 "정답 알려주기"로 고친 해석 (dislike + 정답 JSON)
  - like             : 사용자가 맞다고 확인한 해석
  - pipeline_failure : 파이프라인이 실패·fallback 으로 끝난 이미지
  - pseudo_label     : scripts/pseudo_labeling.py 가 만든 의사 라벨
status : pending → approved | rejected (운영 콘솔 검수)
split  : train | val (승인 시 id 해시로 고정 배정 — 재학습해도 같은 데이터가 같은 쪽)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.learning import LearningBase


class LearningSample(LearningBase):
    __tablename__ = "learning_samples"
    __table_args__ = (UniqueConstraint("origin_id", "kind", name="uq_learning_samples_origin_kind"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # uuid4 hex
    kind: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    split: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)

    # 출처 레코드 (피드백 case_id 또는 의사 라벨 case_id) — 같은 출처를 두 번 적재하지 않기 위한 키
    origin_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    job_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)

    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)  # ParsedPrompt 정답
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 저장소 루트 기준 상대 경로
    label_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 사이드카 JSON 경로

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 검수 메모
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
