"""feedbacks 테이블 조회 (학습 DB).

저장은 services/learning_catalog.record_feedback (피드백 + 파생 학습 샘플을 한 번에) 를 쓴다.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db  # 학습 DB 세션

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
