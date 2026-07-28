"""ORM: 사용자/파이프라인 피드백 레코드.

jobs 와 1:N. job 삭제 시 CASCADE.
source:
  - user              : 프론트 like/dislike
  - pipeline_failure  : 그래프 feedback_collector 자동 저장
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # 부모 job (없으면 FK 위반 — FeedbackService 가 stub job 생성)
    job_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vote: Mapped[str] = mapped_column(String(16), nullable=False)  # like | dislike
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="user")  # user | pipeline_failure
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="feedbacks")  # noqa: F821
