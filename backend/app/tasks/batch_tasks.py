"""
Batch processing tasks (Phase 2).

Scaffold only — enable Celery + Redis when Phase 2 starts.
"""

from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger

# Phase 2:
# from celery import Celery
# from app.core.config import get_settings
# celery_app = Celery("cutnkeep", broker=get_settings().redis_url)


def process_batch_stub(job_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Placeholder for Celery task.
    items: [{ "filename": str, "prompt": str, "path": str }, ...]
    Must process via generator for memory safety (max 500).
    """
    logger.warning(
        "batch_tasks.process_batch_stub called (Phase 2 not implemented) job_id={} n={}",
        job_id,
        len(items),
    )
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "total": len(items),
        "completed": 0,
        "message": "Batch processing is Phase 2. Use /api/v1/upload for single images.",
    }


# @celery_app.task(bind=True, name="process_batch")
# def process_batch(self, job_id: str, items: list[dict]) -> dict:
#     ...
