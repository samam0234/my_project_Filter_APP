"""feedbacks 테이블 영속화.

FeedbackService 가 호출하는 얇은 데이터 접근 계층.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, feedback_id: str) -> Optional[Feedback]:
        """PK 단건."""
        return self.db.get(Feedback, feedback_id)

    def list_by_job(self, job_id: str) -> list[Feedback]:
        """특정 job 의 피드백 최신순."""
        return (
            self.db.query(Feedback)
            .filter(Feedback.job_id == job_id)
            .order_by(Feedback.created_at.desc())
            .all()
        )

    def create(
        self,
        *,
        job_id: str,
        vote: str,
        comment: Optional[str] = None,
        source: str = "user",
        image_path: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
        feedback_id: Optional[str] = None,
    ) -> Feedback:
        """새 피드백 행 insert.

        feedback_id 가 없으면 uuid4.hex 발급.
        (서비스 계층 case_id 와 맞추려면 명시 전달)
        """
        row = Feedback(
            id=feedback_id or uuid4().hex,
            job_id=job_id,
            vote=vote,
            comment=comment,
            source=source,
            image_path=image_path,
            meta=meta or {},
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
