"""Job table persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.job import Job
from app.schemas.response import ProcessResult


class JobRepository:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def get(self, job_id: str) -> Optional[Job]:
        return self.db.get(Job, job_id)

    def create_pending(self, job_id: str, prompt: str) -> Job:
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
        """Insert or update job from pipeline ProcessResult."""
        row = self.get(result.job_id)
        hours = self.settings.file_retention_hours
        expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        parsed = result.parsed_prompt.model_dump() if result.parsed_prompt else None
        meta = result.meta or {}

        if row is None:
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
        row = self.get(job_id)
        if row is None:
            return None
        row.feedback_saved = 1
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[Job]:
        return (
            self.db.query(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )
