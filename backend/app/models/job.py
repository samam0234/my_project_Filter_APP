"""ORM: 처리 Job 레코드.

한 번의 업로드·파이프라인 실행 = jobs 테이블 1행.
id 는 클라이언트에 노출되는 job_id 와 동일(hex uuid).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    # PK = 파이프라인 job_id
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # pending | ok | fallback | failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # ParsedPrompt JSON (target, effect, intensity, crop)
    parsed_prompt: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    # 디스크 경로 (API URL 이 아님)
    before_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    after_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    backend: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # yolo|stub
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    labels: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    confidences: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    feedback_saved: Mapped[int] = mapped_column(Integer, default=0)  # 0/1 (SQLite 호환)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    # 파일 정리 스케줄용 (file_retention_hours)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 1:N 피드백 (job 삭제 시 함께 삭제)
    feedbacks: Mapped[list["Feedback"]] = relationship(  # noqa: F821
        "Feedback",
        back_populates="job",
        cascade="all, delete-orphan",
    )
