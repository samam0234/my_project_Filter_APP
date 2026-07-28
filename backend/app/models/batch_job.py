"""ORM: 배치 Job 레코드 (Phase 2).

여러 이미지를 한 번에 처리하는 배치 단위.
단일 업로드 Job(jobs 테이블) 과 별개 테이블이다.

상태 예: pending | running | done | failed | not_implemented
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # 배치 전체에 공통 적용할 프롬프트 (항목별 override 는 item_results 에)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    total: Mapped[int] = mapped_column(Integer, default=0)  # 총 파일 수
    completed: Mapped[int] = mapped_column(Integer, default=0)  # 처리 완료 수
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0~1.0
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 항목별 결과 스냅샷 목록 (JSON)
    item_results: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)

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
