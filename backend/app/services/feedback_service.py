"""피드백 수집: 파일 사이드카(원본) + 학습 DB(feedbacks · learning_samples).

역할:
  - 사용자 like/dislike API
  - 파이프라인 실패 시 자동 저장 (source=pipeline_failure)

저장 순서 (두 DB 사이 트랜잭션이 없어서 원본 파일을 먼저 남긴다):
  1) data/feedback/{case_id}.jpg + .json  (원본 · 학습 스크립트 입력)
  2) 학습 DB feedbacks + learning_samples  (실패해도 기동 시 sync_from_files 로 복구)
  3) 서비스 DB jobs.feedback_saved = 1
"""

from __future__ import annotations

import json
from contextlib import nullcontext
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
from app.repositories.job_repository import JobRepository
from app.services.learning_catalog import record_feedback, shared_relpath
from app.utils.image_utils import ensure_dir, save_image


class FeedbackService:
    """피드백 영속화 서비스.

    db          : 서비스 DB 세션 (job 조회·feedback_saved 표시). 없으면 내부에서 열고 닫음
    learning_db : 학습 DB 세션. 없으면 app.db.learning.learning_session() 사용
    """

    def __init__(
        self,
        db: Session | None = None,
        settings: Settings | None = None,
        learning_db: Session | None = None,
    ) -> None:
        self._db = db
        self._learning_db = learning_db
        self.settings = settings or get_settings()
        ensure_dir(self.settings.feedback_path)

    def _session(self) -> Tuple[Session, bool]:
        """(서비스 DB session, owned) 반환. owned=True 이면 호출측에서 close 필요."""
        if self._db is not None:
            return self._db, False
        from app.db.session import SessionLocal, get_engine

        SessionLocal.configure(bind=get_engine())
        return SessionLocal(), True

    def _learning(self):
        if self._learning_db is not None:
            return nullcontext(self._learning_db)
        from app.db.learning import learning_session

        return learning_session()

    def save_case(
        self,
        *,
        job_id: str,
        vote: FeedbackVote | str,
        image: Optional[np.ndarray] = None,
        meta: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
        source: str = "user",
        user_id: Optional[str] = None,
    ) -> Tuple[Optional[Feedback], Optional[Path]]:
        """피드백 1건 저장. 반환: (학습 DB 행 또는 None, JSON 사이드카 Path)."""
        # case_id = job_id + 짧은 난수 (파일명·피드백 PK)
        case_id = f"{job_id}_{uuid4().hex[:8]}"
        vote_str = str(vote.value if isinstance(vote, FeedbackVote) else vote)
        meta = dict(meta or {})
        source = str(meta.get("source") or source)
        base = self.settings.feedback_path / case_id
        ensure_dir(self.settings.feedback_path)

        image_path: Optional[Path] = None
        if image is not None:
            image_path = Path(str(base) + ".jpg")
            save_image(image_path, image)

        db, owned = self._session()
        try:
            # --- 서비스 DB 에서 프롬프트·정답·소유자 보강 ---
            # 사용자 피드백 API 는 prompt 를 안 보낸다. parsed_prompt 가 있어야 LoRA·RAG 가 정답으로 쓸 수 있다.
            job_repo = JobRepository(db, self.settings)
            job_row = None
            try:
                job_row = job_repo.get(job_id)
            except Exception:
                logger.exception("피드백 job 조회 실패 job={}", job_id)
            if job_row is not None:
                if not meta.get("prompt") and job_row.prompt:
                    meta["prompt"] = job_row.prompt
                if not meta.get("parsed_prompt") and job_row.parsed_prompt:
                    meta["parsed_prompt"] = job_row.parsed_prompt
                user_id = user_id or job_row.user_id

            # --- 1) 원본 사이드카 ---
            payload: Dict[str, Any] = {
                "case_id": case_id,
                "job_id": job_id,
                "user_id": user_id,
                "vote": vote_str,
                "comment": comment,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "meta": meta,
            }
            if image_path is not None:
                payload["image"] = image_path.name
            json_path = Path(str(base) + ".json")
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            # --- 2) 학습 DB ---
            row: Optional[Feedback] = None
            try:
                with self._learning() as ldb:
                    row = record_feedback(
                        ldb,
                        case_id=case_id,
                        job_id=job_id,
                        vote=vote_str,
                        source=source,
                        comment=comment,
                        meta=meta,
                        user_id=user_id,
                        image_path=shared_relpath(image_path, self.settings),
                        label_path=shared_relpath(json_path, self.settings),
                    )
                logger.info("Feedback saved id={} path={}", row.id, json_path)
            except Exception:
                logger.exception("학습 DB 피드백 저장 실패 (사이드카 유지 → 기동 시 동기화) case={}", case_id)

            # --- 3) 서비스 DB 표시 ---
            if job_row is not None:
                try:
                    job_repo.mark_feedback_saved(job_id)
                except Exception:
                    logger.exception("jobs.feedback_saved 갱신 실패 job={}", job_id)
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
