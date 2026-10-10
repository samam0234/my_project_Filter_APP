"""운영 콘솔 전용 API — /api/v1/console/* (작업 조회 · 학습 데이터 검수)

전체 작업·회원 데이터를 다루므로 **관리자 로그인(CONSOLE_ADMINS)** 또는 **서버 PC(loopback)** 에서만 허용한다
(core/access.require_console). 배포에서는 CONSOLE_REQUIRE_LOGIN=true 로 loopback 도 로그인 필수.
사용자 앱의 /api/v1/jobs 는 로그인 사용자 본인 작업만 돌려준다.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from loguru import logger
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.access import ConsoleActor, require_console
from app.core.config import get_settings
from app.db.learning import get_learning_db, learning_db_mode
from app.db.session import get_db
from app.models.learning_sample import LearningSample
from app.repositories.batch_repository import BatchRepository
from app.repositories.job_repository import JobRepository
from app.routers.jobs import _to_response
from app.schemas.learning import (
    BulkReviewRequest,
    BulkReviewResponse,
    DeleteResponse,
    LearningSampleList,
    LearningSampleResponse,
    ReviewRequest,
)
from app.schemas.response import JobResponse
from app.services import learning_review, system_status, user_admin
from app.services.retention import cleanup_dir
from app.services.learning_review import resolve_file

router = APIRouter(prefix="/console", tags=["console"], dependencies=[Depends(require_console)])


@router.get("/me")
async def console_me(actor: ConsoleActor = Depends(require_console)) -> dict:
    """콘솔 화면이 첫 진입에 부른다 — 401/403 이면 로그인 화면, 200 이면 누구로 들어왔는지 표시."""
    return {"via": actor.via, "username": actor.username}


def _console_view(row) -> JobResponse:
    """사용자용 파일 URL(/files, 소유자 전용) 대신 콘솔 전용 파일 URL 로 바꾼다."""
    res = _to_response(row)
    if res.before_url:
        res.before_url = f"/api/v1/console/files/{row.id}/before"
    if res.after_url:
        res.after_url = f"/api/v1/console/files/{row.id}/after"
    if res.thumb_url:
        res.thumb_url = f"/api/v1/console/files/{row.id}/thumb"
    if res.webp_url:
        res.webp_url = f"/api/v1/console/files/{row.id}/webp"
    return res


@router.get("/jobs", response_model=list[JobResponse])
async def console_jobs(limit: int = 50, db: Session = Depends(get_db)) -> list[JobResponse]:
    """전체 작업 최근 목록 (소유자 무관). limit 상한 200."""
    return [_console_view(r) for r in JobRepository(db).list_recent(limit=min(limit, 200))]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def console_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    row = JobRepository(db).get(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job 없음")
    return _console_view(row)


@router.get("/batches")
async def console_batches(limit: int = 50, db: Session = Depends(get_db)) -> list[dict]:
    """전체 회원의 배치 최근 목록 (상태·진행·실패 수). 이미지는 노출하지 않는다. limit 상한 200."""
    out = []
    for r in BatchRepository(db).list_recent(limit=min(max(limit, 1), 200)):
        items = r.item_results or []
        out.append(
            {
                "job_id": r.id,
                "user_id": r.user_id,
                "status": r.status,
                "progress": r.progress,
                "total": r.total,
                "completed": r.completed,
                "failed": sum(1 for i in items if i.get("status") != "ok"),
                "message": r.message,
                "prompt": r.prompt,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return out


@router.get("/files/{job_id}/{kind}")
async def console_file(job_id: str, kind: str, db: Session = Depends(get_db)) -> FileResponse:
    """작업 before/after/thumb 파일 (소유자 무관). 사진 · 영상 · GIF 모두 — 경로 규칙은 routers/upload.job_file."""
    from app.routers.upload import job_file, media_response

    row = JobRepository(db).get(job_id) if kind in ("before", "after", "thumb", "webp") else None
    path = job_file(row, kind) if row is not None else None
    if path is None:
        raise HTTPException(status_code=404, detail="파일 없음")
    return media_response(path)


# ------------------------------------------------------------------ 학습 데이터 검수 (학습 DB)
# 승인된 문장 샘플만 RAG 예시 · LoRA 학습에 쓰인다 (services/learning_review)


def _sample_view(row, settings) -> LearningSampleResponse:
    res = LearningSampleResponse.model_validate(row)
    if resolve_file(row.image_path, settings) is not None:
        res.has_image = True
        res.image_url = f"/api/v1/console/learning/samples/{row.id}/image"
    return res


@router.get("/learning/stats")
async def learning_stats(ldb: Session = Depends(get_learning_db)) -> dict:
    """출처·상태·split 별 건수 + 학습 DB 모드."""
    return {
        **learning_review.stats(ldb),
        "learning_db": learning_db_mode(),
        "retrain_min_new": get_settings().lora_retrain_min_new,
    }


@router.get("/learning/samples", response_model=LearningSampleList)
async def learning_samples(
    status: Optional[str] = None,
    source: Optional[str] = None,
    kind: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    ldb: Session = Depends(get_learning_db),
) -> LearningSampleList:
    rows, total = learning_review.list_samples(
        ldb, status=status, source=source, kind=kind, q=q, limit=limit, offset=offset
    )
    settings = get_settings()
    return LearningSampleList(
        items=[_sample_view(r, settings) for r in rows], total=total, limit=limit, offset=offset
    )


@router.post("/learning/samples/bulk", response_model=BulkReviewResponse)
async def learning_bulk_review(
    body: BulkReviewRequest,
    ldb: Session = Depends(get_learning_db),
    actor: ConsoleActor = Depends(require_console),
) -> BulkReviewResponse:
    return BulkReviewResponse(**learning_review.bulk_review(ldb, body.ids, body.action, reviewer=actor.label))


@router.post("/learning/samples/{sample_id}/review", response_model=LearningSampleResponse)
async def learning_review_one(
    sample_id: str,
    body: ReviewRequest,
    ldb: Session = Depends(get_learning_db),
    actor: ConsoleActor = Depends(require_console),
) -> LearningSampleResponse:
    try:
        row = learning_review.review(
            ldb, sample_id, body.action, answer=body.answer, note=body.note, reviewer=actor.label
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="샘플 없음")
    except learning_review.ReviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _sample_view(row, get_settings())


@router.delete("/learning/samples/{sample_id}", response_model=DeleteResponse)
async def learning_delete(sample_id: str, ldb: Session = Depends(get_learning_db)) -> DeleteResponse:
    try:
        return DeleteResponse(**learning_review.delete_sample(ldb, sample_id))
    except LookupError:
        raise HTTPException(status_code=404, detail="샘플 없음")


@router.get("/learning/samples/{sample_id}/image")
async def learning_image(sample_id: str, ldb: Session = Depends(get_learning_db)) -> FileResponse:
    row = ldb.get(LearningSample, sample_id)
    path = resolve_file(row.image_path, get_settings()) if row is not None else None
    if path is None:
        raise HTTPException(status_code=404, detail="이미지 없음")
    return FileResponse(path)


# ---------------------------------------------------------------------------- 회원 관리


class DeleteUserRequest(BaseModel):
    # 실수 방지: 지울 회원의 아이디를 그대로 다시 입력
    confirm: str


def _user_admin_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except user_admin.UserAdminError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))


@router.get("/users")
async def list_users(
    q: str = "",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    """회원 목록 + 작업·배치 수 · 활성 세션 · 잠금 여부. 비밀번호 해시는 내보내지 않는다."""
    rows, total = user_admin.list_users(db, q=q, limit=limit, offset=offset)
    return {"items": [asdict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.post("/users/{user_id}/unlock")
async def unlock_user(user_id: str, db: Session = Depends(get_db)) -> dict:
    user = _user_admin_call(user_admin.unlock, db, user_id)
    return {"id": user.id, "locked": False}


@router.post("/users/{user_id}/sessions/revoke")
async def revoke_user_sessions(user_id: str, db: Session = Depends(get_db)) -> dict:
    return {"id": user_id, "revoked": _user_admin_call(user_admin.revoke_sessions, db, user_id)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    body: DeleteUserRequest,
    db: Session = Depends(get_db),
    ldb: Session = Depends(get_learning_db),
    actor: ConsoleActor = Depends(require_console),
) -> dict:
    """계정·작업·배치·영상·파일 삭제 (되돌릴 수 없음). 학습 샘플은 계정 연결만 끊는다."""
    return _user_admin_call(
        user_admin.delete_user, db, ldb, user_id, confirm=body.confirm, actor_username=actor.username
    )


# ---------------------------------------------------------------------------- 시스템


@router.get("/system")
async def system_snapshot() -> dict:
    """세그·오픈보캐브·LLM·배치 큐·영상·콘솔 설정, 저장 공간, 배포 설정 점검 결과. 모델을 새로 로드하지 않는다."""
    return await run_in_threadpool(system_status.snapshot)


@router.post("/system/cleanup")
async def system_cleanup(
    dry_run: bool = False,
    actor: ConsoleActor = Depends(require_console),
) -> dict:
    """FILE_RETENTION_HOURS 보다 오래된 업로드 파일 정리 (scripts/cleanup.py 와 같은 함수). dry_run 이면 집계만."""
    settings = get_settings()
    from app.services.feedback_images import purge_expired

    result = await run_in_threadpool(
        cleanup_dir, settings.upload_path, settings.file_retention_hours, dry_run=dry_run
    )
    feedback = await run_in_threadpool(purge_expired, settings, dry_run=dry_run)
    if not dry_run:
        logger.info(
            "업로드 정리 by={} files={} bytes={} feedback_images={}", actor.label, result.removed_files, result.freed_bytes,
            feedback["removed_files"],
        )
    return result.as_dict() | {"retention_hours": settings.file_retention_hours, "feedback_images": feedback}
