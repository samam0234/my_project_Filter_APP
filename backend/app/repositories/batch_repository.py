"""batch_jobs 테이블 영속화 (Phase 2).

배치 생성·진행률 갱신. 실제 이미지 처리는 tasks.batch_tasks 가 담당.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.batch_job import BatchJob


class BatchRepository:
    """BatchJob ORM CRUD."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, batch_id: str) -> Optional[BatchJob]:
        """PK 단건 조회."""
        return self.db.get(BatchJob, batch_id)

    def create(
        self,
        *,
        batch_id: str,
        prompt: str,
        total: int,
        status: str = "not_implemented",
        message: Optional[str] = None,
    ) -> BatchJob:
        """새 배치 행 생성. Phase 1 stub 은 status=not_implemented 가 기본."""
        row = BatchJob(
            id=batch_id,
            prompt=prompt,
            total=total,
            completed=0,
            progress=0.0,
            status=status,
            message=message,
            item_results=[],
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update_progress(
        self,
        batch_id: str,
        *,
        completed: int,
        progress: float,
        status: str,
        item_results: Optional[list[Any]] = None,
        message: Optional[str] = None,
    ) -> Optional[BatchJob]:
        """워커가 진행 중/완료 시 호출 (Phase 2). 없으면 None."""
        row = self.get(batch_id)
        if row is None:
            return None
        row.completed = completed
        row.progress = progress
        row.status = status
        if item_results is not None:
            row.item_results = item_results
        if message is not None:
            row.message = message
        self.db.commit()
        self.db.refresh(row)
        return row
