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

    # =============================================================================
    # [하드코딩 파트] 배치 실처리 워커
    # -----------------------------------------------------------------------------
    # [임무] 다장 순회 처리 + batch_jobs 진행률 갱신 (Phase2)
    # [연결] run_pipeline / ImageProcessor, BatchRepository, routers.batch, redis
    # [규칙] 장당 처리·해제. 실패 정책 명시. Celery 시 compose worker 활성화.
    # [힌트] for item in items: run_pipeline(...); update_progress(...)
    # =============================================================================
    # >>> 여기에 배치 실처리 작성 <<<
    #

    # =============================================================================
    # [이미 구현된 구간 · 바이브] stub 응답 (미구현 표시용)
    # =============================================================================
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
