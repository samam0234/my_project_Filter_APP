"""배치 처리 작업 (Phase 2).

회원 배치를 한 장씩 처리하고 batch_jobs 진행률을 갱신한다.
BATCH_USE_CELERY=true 이고 celery 가 설치돼 있으면 Redis 워커로 넘긴다.
아니면 라우터의 BackgroundTasks 가 같은 run_batch_job 을 호출한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.repositories.batch_repository import BatchRepository
from app.schemas.request import ParsedPrompt

# Celery CLI 가 모듈 속성 `celery` 를 찾는다. 미설치면 None.
celery = None
run_batch_job_task = None


def batch_dir(job_id: str, settings: Settings | None = None) -> Path:
    """배치 파일 루트: uploads/batches/{job_id}."""
    settings = settings or get_settings()
    return settings.upload_path / "batches" / job_id


def write_manifest(
    job_id: str,
    items: List[Dict[str, Any]],
    settings: Settings | None = None,
) -> Path:
    """항목 파일명·상대경로를 기록한다."""
    root = batch_dir(job_id, settings)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "manifest.json"
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


def _load_manifest(job_id: str, settings: Settings) -> list[dict]:
    path = batch_dir(job_id, settings) / "manifest.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _save_result_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    cv2.imwrite(str(path), image)


def run_batch_job(
    job_id: str,
    *,
    session_factory: Callable | None = None,
    processor=None,
    settings: Settings | None = None,
    parsed: ParsedPrompt | None = None,
) -> Dict[str, Any]:
    """매니페스트의 이미지를 한 장씩 처리하고 진행률을 커밋한다.

    항목 하나의 실패가 나머지를 중단하지 않는다.
    """
    settings = settings or get_settings()
    factory = session_factory or SessionLocal
    db = factory()
    try:
        repo = BatchRepository(db)
        row = repo.get(job_id)
        if row is None:
            return {
                "job_id": job_id,
                "status": "not_found",
                "total": 0,
                "completed": 0,
                "message": "배치 job 없음",
            }
        manifest = _load_manifest(job_id, settings)
        total = len(manifest)
        repo.update_progress(
            job_id,
            completed=0,
            progress=0.0,
            status="running",
            message="처리 중",
            item_results=[],
        )
        if processor is None:
            from app.services.image_processor import ImageProcessor

            processor = ImageProcessor(settings)
        if parsed is None:
            from app.services.prompt_llm import parse_prompt_or_heuristic

            parsed = parse_prompt_or_heuristic(row.prompt or "", settings)
        root = batch_dir(job_id, settings)
        results: list[dict] = []
        completed = 0
        failed = 0
        for item in manifest:
            name = str(item.get("filename") or item.get("relpath") or completed)
            rel = str(item.get("relpath") or "")
            completed += 1
            try:
                data = (root / rel).read_bytes()
                output = next(processor.process_batch_generator([(data, parsed)]))
                out_name = f"{int(item.get('index', completed)):04d}.jpg"
                _save_result_image(root / "out" / out_name, output.result)
                ok = bool(output.validation.ok)
                if not ok:
                    failed += 1
                results.append(
                    {
                        "filename": name,
                        "status": "ok" if ok else "fallback",
                        "backend": output.seg.backend,
                        "message": output.validation.message,
                        "output": f"out/{out_name}",
                    }
                )
            except Exception as exc:
                failed += 1
                logger.exception("배치 항목 실패 job={} file={}", job_id, name)
                results.append(
                    {"filename": name, "status": "failed", "message": str(exc)[:300]}
                )
            repo.update_progress(
                job_id,
                completed=completed,
                progress=(completed / total) if total else 1.0,
                status="running",
                item_results=results,
                message=f"{completed}/{total}",
            )
        if total == 0:
            status, message = "failed", "처리할 파일이 없습니다."
        elif failed == total:
            status, message = "failed", "모든 항목이 실패했습니다."
        elif failed:
            status, message = "done", f"완료 (실패 {failed}/{total})"
        else:
            status, message = "done", "완료"
        repo.update_progress(
            job_id,
            completed=completed,
            progress=1.0 if total else 0.0,
            status=status,
            item_results=results,
            message=message,
        )
        return {
            "job_id": job_id,
            "status": status,
            "total": total,
            "completed": completed,
            "message": message,
        }
    finally:
        db.close()


def enqueue_batch(job_id: str) -> bool:
    """Celery 로 넘기면 True. 플래그·패키지가 없으면 False (호출측이 직접 실행)."""
    settings = get_settings()
    if not settings.batch_use_celery or celery is None or run_batch_job_task is None:
        return False
    run_batch_job_task.delay(job_id)
    return True


def process_batch_stub(job_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """하위 호환. 매니페스트가 있으면 실처리, 파일 없이 호출되면 미구현 응답."""
    if (batch_dir(job_id) / "manifest.json").is_file():
        return run_batch_job(job_id)
    logger.warning("batch stub 호출 (파일 없음) job_id={} n={}", job_id, len(items))
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "total": len(items),
        "completed": 0,
        "message": "배치 파일이 없습니다. POST /api/v1/batch 로 등록하세요.",
    }


try:
    from celery import Celery as _Celery
except ImportError:
    pass
else:
    _broker = get_settings().redis_url
    celery = _Celery("cutnkeep", broker=_broker, backend=_broker)

    @celery.task(name="cutnkeep.run_batch_job")
    def run_batch_job_task(job_id: str) -> dict:
        return run_batch_job(job_id)
