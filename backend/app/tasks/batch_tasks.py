"""
배치 처리 작업 (Phase 2).

스캐폴드만 — Phase 2에서 Celery + Redis 활성화.
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
    Celery 작업 placeholder.
    items: [{ "filename": str, "prompt": str, "path": str }, ...]
    메모리 안전을 위해 generator로 처리 (최대 500).
    """
    logger.warning(
        "batch stub 호출 (Phase 2 미구현) job_id={} n={}",
        job_id,
        len(items),
    )
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "total": len(items),
        "completed": 0,
        "message": "배치는 Phase 2. 단일 이미지는 /api/v1/upload 사용.",
    }


# @celery_app.task(bind=True, name="process_batch")
# def process_batch(self, job_id: str, items: list[dict]) -> dict:
#     ...
