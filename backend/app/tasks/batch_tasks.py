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

    # ---
    # 제목 (하드코딩 파트 부분 : [배치 실처리 워커])
    # [관련 작업 임무 및 역할]
    #   여러 장 이미지를 순회 처리하고 batch_jobs 진행률을 갱신한다.
    #   완성도 스케치 Phase2 부족분(~80% 중 배치 축).
    # [기능하고 연결된 변수 및 함수]
    #   - 입력: job_id, items[{filename, prompt, path}, ...]
    #   - 파이프: app.workflows.graph.run_pipeline 또는 ImageProcessor.run
    #   - DB: BatchRepository.update_progress / create
    #   - 라우터: app.routers.batch
    #   - 설정: get_settings().redis_url, constants 배치 상한
    # [작성해야 하는 방식 및 규칙]
    #   1) Phase1 단일 /upload 가 안정된 뒤에 구현.
    #   2) 한 번에 전부 장을 메모리에 올리지 말 것 — 장당 처리 후 해제.
    #   3) 장 실패는 전체 중단 vs 스킵 정책을 정하고 item_results 에 기록.
    #   4) status: pending → running → completed|failed 흐름 유지.
    #   5) Celery 쓸 경우 broker=redis, compose celery_worker 활성화.
    # [코드 방식 힌트]
    #   completed = 0
    #   results = []
    #   for item in items:
    #       try:
    #           out = run_pipeline(image_bytes=..., prompt=item["prompt"])
    #           results.append({"ok": True, **out})
    #           completed += 1
    #       except Exception as e:
    #           results.append({"ok": False, "error": str(e)})
    #       # BatchRepository.update_progress(job_id, completed, total)
    #   return {"job_id": job_id, "status": "completed", "total": len(items),
    #           "completed": completed, "item_results": results}
    # ---
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
