"""ORM: processing job records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parsed_prompt: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    before_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    after_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    backend: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    labels: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    confidences: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    feedback_saved: Mapped[int] = mapped_column(Integer, default=0)  # 0/1 for SQLite compat
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
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    feedbacks: Mapped[list["Feedback"]] = relationship(  # noqa: F821
        "Feedback",
        back_populates="job",
        cascade="all, delete-orphan",
    )
