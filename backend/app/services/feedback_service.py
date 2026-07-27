"""Feedback collection: save failure/dislike cases as image + JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.core.constants import FeedbackVote
from app.utils.image_utils import ensure_dir, save_image


class FeedbackService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        ensure_dir(self.settings.feedback_path)

    def save_case(
        self,
        *,
        job_id: str,
        vote: FeedbackVote | str,
        image: Optional[np.ndarray] = None,
        meta: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
    ) -> Path:
        """Persist feedback case under data/feedback/{id}.json (+ optional image)."""
        case_id = f"{job_id}_{uuid4().hex[:8]}"
        base = self.settings.feedback_path / case_id
        ensure_dir(self.settings.feedback_path)

        payload: Dict[str, Any] = {
            "case_id": case_id,
            "job_id": job_id,
            "vote": str(vote.value if isinstance(vote, FeedbackVote) else vote),
            "comment": comment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": meta or {},
        }

        image_path: Optional[Path] = None
        if image is not None:
            image_path = Path(str(base) + ".jpg")
            save_image(image_path, image)
            payload["image"] = image_path.name

        json_path = Path(str(base) + ".json")
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Feedback saved: {}", json_path)
        return json_path

    def save_failure(
        self,
        *,
        job_id: str,
        image: Optional[np.ndarray],
        meta: Dict[str, Any],
    ) -> Path:
        return self.save_case(
            job_id=job_id,
            vote=FeedbackVote.DISLIKE,
            image=image,
            meta={**meta, "source": "pipeline_failure"},
        )
