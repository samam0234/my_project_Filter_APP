"""
배치 처리 작업 (Phase 2).

스캐폴드만 — Phase 2에서 Celery + Redis 활성화.
현재 process_batch_stub 은 라우터에서 메타 기록용으로만 호출된다.
"""

from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger

# Phase 2 예시 (아직 비활성):
# from celery import Celery
# from app.core.config import get_settings
# celery_app = Celery("cutnkeep", broker=get_settings().redis_url)


def process_batch_stub(job_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Celery 작업 placeholder.

    items: [{ "filename": str, "prompt": str, "path": str }, ...]
    실제 구현 시 메모리 안전을 위해 generator 로 한 장씩 처리 (최대 500).

    반환 dict 는 BatchRepository.create 상태 필드에 매핑된다.
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


# Phase 2 실제 태스크 스케치:
# @celery_app.task(bind=True, name="process_batch")
# def process_batch(self, job_id: str, items: list[dict]) -> dict:
#     ...
