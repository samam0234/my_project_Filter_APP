"""ORM: 사용자/파이프라인 피드백 이벤트 (학습 DB).

서비스 DB 의 jobs 와는 DB 가 달라 FK 가 없다 — job_id · user_id 는 값으로만 보관.
원본은 data/feedback/{id}.json 사이드카 (이미지는 파일, DB 에는 경로만).
source:
  - user              : 프론트 like/dislike
  - pipeline_failure  : 그래프 feedback_collector 자동 저장
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.learning import LearningBase


class Feedback(LearningBase):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # case_id = 사이드카 파일명
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    vote: Mapped[str] = mapped_column(String(16), nullable=False)  # like | dislike
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="user", index=True)  # user | pipeline_failure
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 저장소 루트 기준 상대 경로
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
