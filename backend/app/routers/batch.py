"""배치 처리 라우터. 로그인 회원 전용.

파일을 디스크에 저장하고 상태를 queued 로 남긴 뒤,
Celery(BATCH_USE_CELERY) 또는 프로세스 안 BackgroundTasks 로 한 장씩 처리한다.
"""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.constants import MAX_BATCH_SIZE
from app.core.deps import current_user
from app.core.security import validate_upload_file
from app.db.session import get_db
from app.exceptions import FileValidationError, to_http_exception
from app.models.user import User
from app.repositories.batch_repository import BatchRepository
from app.tasks.batch_tasks import _load_manifest, batch_dir, enqueue_batch, run_batch_job, write_manifest
from app.core.config import get_settings

router = APIRouter(tags=["batch"])


@router.post("/batch")
async def create_batch(
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    prompt: str = Form(default="person remove background"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """여러 파일을 한 배치로 등록하고 처리를 시작한다.

    - 파일 개수 상한: MAX_BATCH_SIZE
    - 바이트는 uploads/batches/{job_id}/items 에 저장
    - 응답은 바로 queued. 진행률은 GET /batch/{job_id}
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파일이 없습니다.")
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Max batch size is {MAX_BATCH_SIZE}",
        )
    job_id = uuid4().hex
    root = batch_dir(job_id)
    (root / "items").mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    try:
        for index, file in enumerate(files):
            try:
                data = await validate_upload_file(file)
            except FileValidationError as exc:
                raise to_http_exception(exc) from exc
            suffix = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
            rel = f"items/{index:04d}{suffix}"
            (root / rel).write_bytes(data)
            manifest.append(
                {
                    "index": index,
                    "filename": Path(file.filename or rel).name,
                    "relpath": rel,
                }
            )
        write_manifest(job_id, manifest)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    try:
        BatchRepository(db).create(
            user_id=user.id,
            batch_id=job_id,
            prompt=prompt,
            total=len(manifest),
            status="queued",
            message="대기",
        )
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    if not enqueue_batch(job_id):
        background.add_task(run_batch_job, job_id)
    return {
        "job_id": job_id,
        "status": "queued",
        "total": len(manifest),
        "completed": 0,
        "message": "배치가 대기열에 들어갔습니다.",
    }


@router.get("/batch/{job_id}")
async def get_batch_status(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """본인 배치 진행률 조회. 없거나 남의 배치면 not_found."""
    row = BatchRepository(db).get(job_id)
    if row is None or row.user_id != user.id:
        return {
            "job_id": job_id,
            "status": "not_found",
            "progress": 0.0,
            "message": "배치 job 없음.",
        }
    base = f"/api/v1/batch/{row.id}"
    items = []
    for n, item in enumerate(row.item_results or []):
        index = int(item.get("index", n))
        items.append(
            {
                **item,
                "index": index,
                "before_url": f"{base}/items/{index}/before",
                "after_url": f"{base}/items/{index}/after" if item.get("output") else None,
            }
        )
    return {
        "job_id": row.id,
        "status": row.status,
        "progress": row.progress,
        "total": row.total,
        "completed": row.completed,
        "message": row.message,
        "prompt": row.prompt,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "item_results": items,
        "download_url": f"{base}/download" if any(i.get("output") for i in items) else None,
    }


@router.get("/batch")
async def list_my_batches(
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """내 배치 목록 (최신순). 배치 ID 를 기억하지 않아도 다시 찾을 수 있게."""
    rows = BatchRepository(db).list_for_user(user.id, limit=min(max(limit, 1), 100))
    return [
        {
            "job_id": r.id,
            "status": r.status,
            "progress": r.progress,
            "total": r.total,
            "completed": r.completed,
            "message": r.message,
            "prompt": r.prompt,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def _owned_batch(db: Session, job_id: str, user: User):
    row = BatchRepository(db).get(job_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="배치를 찾을 수 없습니다.")
    return row


@router.get("/batch/{job_id}/items/{index}/{kind}")
async def get_batch_item_image(
    job_id: str,
    index: int,
    kind: Literal["before", "after"],
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """배치 항목의 원본(before) · 결과(after) 이미지. 본인 배치만 (남의 것은 404)."""
    row = _owned_batch(db, job_id, user)
    root = batch_dir(row.id)
    if kind == "before":
        entry = next((m for m in _load_manifest(row.id, get_settings()) if int(m.get("index", -1)) == index), None)
        rel = str(entry.get("relpath")) if entry else ""
    else:
        entry = next((r for r in (row.item_results or []) if int(r.get("index", -1)) == index), None)
        rel = str(entry.get("output") or "") if entry else ""
    path = (root / rel).resolve() if rel else None
    if path is None or not path.is_file() or not path.is_relative_to(root.resolve()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이미지를 찾을 수 없습니다.")
    return FileResponse(path)


@router.get("/batch/{job_id}/download")
async def download_batch(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """처리된 결과 이미지를 zip 으로. 파일명은 원본 이름 기준 (같은 이름이면 번호를 붙임)."""
    row = _owned_batch(db, job_id, user)
    root = batch_dir(row.id).resolve()
    buf = io.BytesIO()
    used: set[str] = set()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for item in sorted(row.item_results or [], key=lambda r: int(r.get("index", 0))):
            rel = item.get("output")
            path = (root / str(rel)).resolve() if rel else None
            if path is None or not path.is_file() or not path.is_relative_to(root):
                continue
            stem = Path(str(item.get("filename") or path.stem)).stem
            name = f"{stem}_result{path.suffix}"
            if name in used:
                name = f"{stem}_{int(item.get('index', count)):04d}_result{path.suffix}"
            used.add(name)
            zf.write(path, name)
            count += 1
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="받을 결과가 없습니다.")
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="cutnkeep_batch_{row.id[:8]}.zip"'},
    )
