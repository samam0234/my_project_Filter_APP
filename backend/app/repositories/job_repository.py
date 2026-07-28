"""jobs 테이블 영속화.

라우터·FeedbackService 가 공통으로 사용하는 Job CRUD.
SQLAlchemy Session 을 생성자에서 주입받는다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.job import Job
from app.schemas.response import ProcessResult


class JobRepository:
    """Job ORM 행에 대한 데이터 접근 계층."""

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def get(self, job_id: str) -> Optional[Job]:
        """PK 로 단건 조회 (없으면 None)."""
        return self.db.get(Job, job_id)

    def create_pending(self, job_id: str, prompt: str) -> Job:
        """처리 전 pending 행 생성.

        피드백 FK 를 위해 job 이 없을 때 stub 으로도 사용한다.
        expires_at 은 file_retention_hours 기준.
        """
        hours = self.settings.file_retention_hours
        expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        row = Job(
            id=job_id,
            prompt=prompt,
            status="pending",
            quality_score=0.0,
            feedback_saved=0,
            expires_at=expires,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_result(self, result: ProcessResult, prompt: str) -> Job:
        """파이프라인 ProcessResult로 job을 삽입 또는 갱신.

        이미 행이 있으면 덮어쓰고, 없으면 새로 insert.
        """
        row = self.get(result.job_id)
        hours = self.settings.file_retention_hours
        expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        parsed = result.parsed_prompt.model_dump() if result.parsed_prompt else None
        meta = result.meta or {}

        if row is None:
            # 신규 삽입
            row = Job(
                id=result.job_id,
                prompt=prompt,
                status=result.status,
                parsed_prompt=parsed,
                quality_score=result.quality_score,
                before_path=result.before_path,
                after_path=result.after_path,
                backend=meta.get("backend"),
                message=result.message,
                labels=meta.get("labels"),
                confidences=meta.get("confidences"),
                feedback_saved=1 if result.feedback_saved else 0,
                error=result.message if result.status == "failed" else None,
                expires_at=expires,
            )
            self.db.add(row)
        else:
            # 기존 행 갱신
            row.prompt = prompt
            row.status = result.status
            row.parsed_prompt = parsed
            row.quality_score = result.quality_score
            row.before_path = result.before_path
            row.after_path = result.after_path
            row.backend = meta.get("backend")
            row.message = result.message
            row.labels = meta.get("labels")
            row.confidences = meta.get("confidences")
            row.feedback_saved = 1 if result.feedback_saved else 0
            row.error = result.message if result.status == "failed" else None
            row.expires_at = expires

        self.db.commit()
        self.db.refresh(row)
        return row

    def mark_feedback_saved(self, job_id: str) -> Optional[Job]:
        """피드백이 저장된 뒤 job.feedback_saved = 1."""
        row = self.get(job_id)
        if row is None:
            return None
        row.feedback_saved = 1
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[Job]:
        """최신 생성 순 목록 (콘솔/운영 조회)."""
        return (
            self.db.query(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )
