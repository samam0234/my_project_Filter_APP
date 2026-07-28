"""피드백 수집: DB(레포지토리) + 선택적 이미지/JSON 사이드카.

역할:
  - 사용자 like/dislike API
  - 파이프라인 실패 시 자동 저장 (source=pipeline_failure)

저장 위치:
  1) SQL jobs/feedback 테이블 (MariaDB 또는 SQLite)
  2) data/feedback/{case_id}.jpg + .json  (학습·디버그용 파일)
"""

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
    """피드백 영속화 서비스.

    db 세션을 주입받으면 요청 스코프 세션을 재사용하고,
    없으면 내부에서 SessionLocal 을 열어 owned=True 로 close 한다.
    """

    def __init__(
        self,
        db: Session | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._db = db
        self.settings = settings or get_settings()
        ensure_dir(self.settings.feedback_path)

    def _session(self) -> Tuple[Session, bool]:
        """(session, owned) 반환. owned=True 이면 호출측에서 close 필요."""
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
        레포지토리를 통해 MariaDB/SQLite에 피드백 저장.
        학습용으로 data/feedback/ 에 이미지+JSON 사이드카도 선택 저장.

        반환: (DB row 또는 None, JSON 사이드카 Path 또는 None)
        DB 실패해도 파일 사이드카는 남겨 둔다.
        """
        # case_id = job_id + 짧은 난수 (파일명·피드백 PK 후보)
        case_id = f"{job_id}_{uuid4().hex[:8]}"
        vote_str = str(vote.value if isinstance(vote, FeedbackVote) else vote)
        meta = meta or {}
        source = str(meta.get("source") or source)

        image_path: Optional[Path] = None
        json_path: Optional[Path] = None
        base = self.settings.feedback_path / case_id
        ensure_dir(self.settings.feedback_path)

        # --- 파일 사이드카 (이미지) ---
        if image is not None:
            image_path = Path(str(base) + ".jpg")
            save_image(image_path, image)

        # --- 파일 사이드카 (JSON 메타) ---
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

        # --- DB 저장 ---
        db, owned = self._session()
        row: Optional[Feedback] = None
        try:
            # 부모 job 존재 확인 (FK) — 없으면 stub 생성
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
            # job 행에 feedback_saved 플래그 표시
            job_repo.mark_feedback_saved(job_id)
            logger.info("Feedback saved db_id={} path={}", row.id, json_path)
        except Exception:
            logger.exception("DB 피드백 저장 실패 (파일 사이드카는 유지)")
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
        """파이프라인 실패/fallback 소진 시 dislike 로 자동 기록."""
        return self.save_case(
            job_id=job_id,
            vote=FeedbackVote.DISLIKE,
            image=image,
            meta={**meta, "source": "pipeline_failure"},
            source="pipeline_failure",
        )
