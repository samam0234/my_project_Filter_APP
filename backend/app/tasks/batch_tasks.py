"""배치 처리 작업 (Phase 2).

회원 배치를 한 장씩 처리하고 batch_jobs 진행률을 갱신한다.
BATCH_USE_CELERY=true 이고 celery 가 설치돼 있으면 Redis 워커로 넘긴다.
아니면 라우터의 BackgroundTasks 가 같은 run_batch_job 을 호출한다.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List

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


def _store_output(job_dir: Path, out_dir: Path, index: int) -> str | None:
    """파이프라인이 만든 결과 파일을 배치 폴더(out/)로 옮기고 상대 경로를 돌려준다. 없으면 None."""
    for name in ("after.png", "after.jpg"):
        src = job_dir / name
        if src.is_file():
            out_dir.mkdir(parents=True, exist_ok=True)
            dst = out_dir / f"{index:04d}{src.suffix}"
            shutil.move(str(src), str(dst))
            return f"out/{dst.name}"
    return None


def run_batch_job(
    job_id: str,
    *,
    session_factory: Callable | None = None,
    settings: Settings | None = None,
    parsed: ParsedPrompt | None = None,
) -> Dict[str, Any]:
    """매니페스트의 이미지를 한 장씩 처리하고 진행률을 커밋한다.

    한 장 한 장이 **단일 업로드와 같은 파이프라인**(workflows.graph.run_pipeline)을 탄다 —
    인스턴스 선택(위치·순서·색), 마스크 원본 크기 복원, 재시도·최선 시도 채택이 똑같이 적용된다.
    문장은 한 번만 해석해 모든 장에 넘기고(LLM 호출 1회), 세그 모델은 프로세스 공용 싱글톤을 쓴다.
    항목 하나의 실패가 나머지를 중단하지 않는다. 실패 케이스는 학습 후보로 저장하지 않는다(대량 등록 방지).
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
                from app.workflows.graph import run_pipeline

                data = (root / rel).read_bytes()
                index = int(item.get("index", completed - 1))
                result = run_pipeline(data, row.prompt or "", parsed=parsed, persist=False)
                stored = _store_output(settings.upload_path / result.job_id, root / "out", index)
                shutil.rmtree(settings.upload_path / result.job_id, ignore_errors=True)  # 임시 작업 폴더
                ok = result.status == "ok" and stored is not None
                if not ok:
                    failed += 1
                results.append(
                    {
                        "index": index,
                        "filename": name,
                        "status": result.status if stored else "failed",
                        "backend": (result.meta or {}).get("backend"),
                        "quality_score": round(result.quality_score, 3),
                        "message": result.message,
                        "output": stored,
                    }
                )
            except Exception as exc:
                failed += 1
                logger.exception("배치 항목 실패 job={} file={}", job_id, name)
                results.append(
                    {
                        "index": int(item.get("index", completed - 1)),
                        "filename": name,
                        "status": "failed",
                        "message": str(exc)[:300],
                        "output": None,
                    }
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
