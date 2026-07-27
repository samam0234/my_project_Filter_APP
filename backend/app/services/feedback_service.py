"""Feedback collection: DB (repository) + optional image/JSON sidecar on disk."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import numpy as np
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import FeedbackVote
from app.models.feedback import Feedback
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.job_repository import JobRepository
from app.utils.image_utils import ensure_dir, save_image


class FeedbackService:
    def __init__(
        self,
        db: Session | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._db = db
        self.settings = settings or get_settings()
        ensure_dir(self.settings.feedback_path)

    def _session(self) -> Tuple[Session, bool]:
        """Return (session, owned). Owned sessions must be closed by caller."""
        if self._db is not None:
            return self._db, False
        from app.db.session import SessionLocal, get_engine

        SessionLocal.configure(bind=get_engine())
        return SessionLocal(), True

    def save_case(
        self,
        *,
        job_id: str,
        vote: FeedbackVote | str,
        image: Optional[np.ndarray] = None,
        meta: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
        source: str = "user",
    ) -> Tuple[Optional[Feedback], Optional[Path]]:
        """
        Persist feedback to MariaDB/SQLite via repository.
        Also writes optional sidecar image + JSON under data/feedback/ for training dumps.
        """
        case_id = f"{job_id}_{uuid4().hex[:8]}"
        vote_str = str(vote.value if isinstance(vote, FeedbackVote) else vote)
        meta = meta or {}
        source = str(meta.get("source") or source)

        image_path: Optional[Path] = None
        json_path: Optional[Path] = None
        base = self.settings.feedback_path / case_id
        ensure_dir(self.settings.feedback_path)

        if image is not None:
            image_path = Path(str(base) + ".jpg")
            save_image(image_path, image)

        payload: Dict[str, Any] = {
            "case_id": case_id,
            "job_id": job_id,
            "vote": vote_str,
            "comment": comment,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": meta,
        }
        if image_path is not None:
            payload["image"] = image_path.name

        json_path = Path(str(base) + ".json")
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        db, owned = self._session()
        row: Optional[Feedback] = None
        try:
            # Ensure parent job exists (feedback FK) — create stub if missing
            job_repo = JobRepository(db, self.settings)
            if job_repo.get(job_id) is None:
                job_repo.create_pending(job_id, prompt=str(meta.get("prompt") or ""))
            row = FeedbackRepository(db).create(
                job_id=job_id,
                vote=vote_str,
                comment=comment,
                source=source,
                image_path=str(image_path) if image_path else None,
                meta=meta,
                feedback_id=case_id,
            )
            job_repo.mark_feedback_saved(job_id)
            logger.info("Feedback saved db_id={} path={}", row.id, json_path)
        except Exception:
            logger.exception("Failed to persist feedback to DB (file sidecar kept)")
            if owned:
                db.rollback()
        finally:
            if owned:
                db.close()

        return row, json_path

    def save_failure(
        self,
        *,
        job_id: str,
        image: Optional[np.ndarray],
        meta: Dict[str, Any],
    ) -> Tuple[Optional[Feedback], Optional[Path]]:
        return self.save_case(
            job_id=job_id,
            vote=FeedbackVote.DISLIKE,
            image=image,
            meta={**meta, "source": "pipeline_failure"},
            source="pipeline_failure",
        )
