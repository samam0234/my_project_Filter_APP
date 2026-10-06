"""학습 데이터 검수 — 운영 콘솔의 승인 · 거절 · 정답 수정 · 삭제.

승인(approved)된 prompt 샘플만 RAG 예시와 LoRA 학습에 쓰인다.
잘못된 교정 하나가 비슷한 요청 전체의 해석을 바꾸는 것을 막기 위한 관문.

삭제는 "다시 생기지 않게" 처리한다:
  - 원본 파일(피드백 사이드카 json·jpg, 의사 라벨 json)을 지운다
  - 피드백 행은 남은 샘플이 없으면 지운다
  - 샘플 행은 status=deleted 로 남기고 문장·정답·경로를 비운다 (기동 시 동기화가 되살리지 않도록 표식만 유지)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.feedback import Feedback
from app.models.learning_sample import LearningSample
from app.services.learning_catalog import assign_split, parse_answer

STATUSES = ("pending", "approved", "rejected", "deleted")
USER_SOURCES = ("correction", "like", "request")


class ReviewError(ValueError):
    """검수 요청이 잘못됨 (정답 형식 등) → 400."""


def list_samples(
    db: Session,
    *,
    status: Optional[str] = None,
    source: Optional[str] = None,
    kind: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[LearningSample], int]:
    query = db.query(LearningSample)
    if status:
        query = query.filter(LearningSample.status == status)
    else:
        query = query.filter(LearningSample.status != "deleted")
    if source:
        # "user" = 사용자에게서 온 데이터 (교정·좋아요·회원 요청) — 의사 라벨 수천 건에 묻히지 않게
        sources = USER_SOURCES if source == "user" else tuple(s for s in source.split(",") if s)
        query = query.filter(LearningSample.source.in_(sources))
    if kind:
        query = query.filter(LearningSample.kind == kind)
    if q:
        query = query.filter(LearningSample.prompt.contains(q))
    total = query.count()
    rows = (
        query.order_by(LearningSample.created_at.desc(), LearningSample.id)
        .offset(max(0, offset))
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return rows, total


def stats(db: Session) -> dict:
    """출처·상태·split 별 건수."""
    out: dict = {"by_status": {}, "by_source": {}, "approved_by_split": {}}
    for status, n in db.query(LearningSample.status, func.count()).group_by(LearningSample.status):
        out["by_status"][status] = n
    for source, status, n in (
        db.query(LearningSample.source, LearningSample.status, func.count())
        .group_by(LearningSample.source, LearningSample.status)
    ):
        out["by_source"].setdefault(source, {})[status] = n
    for split, n in (
        db.query(LearningSample.split, func.count())
        .filter(LearningSample.status == "approved")
        .group_by(LearningSample.split)
    ):
        out["approved_by_split"][split or "none"] = n
    return out


def _get(db: Session, sample_id: str) -> LearningSample:
    row = db.get(LearningSample, sample_id)
    if row is None or row.status == "deleted":
        raise LookupError(sample_id)
    return row


def _approve(row: LearningSample, answer: Optional[dict], reviewer: str) -> None:
    if answer is not None:
        parsed = parse_answer(answer)
        if parsed is None:
            raise ReviewError("정답 형식이 올바르지 않습니다 (ParsedPrompt JSON).")
        row.answer = parsed
    if row.kind == "prompt" and not row.answer:
        raise ReviewError("정답이 없는 문장 샘플은 승인할 수 없습니다. 정답을 입력하세요.")
    row.status = "approved"
    row.split = row.split or assign_split(row.id)
    row.reviewed_by = reviewer
    row.reviewed_at = datetime.now(timezone.utc)


def review(
    db: Session,
    sample_id: str,
    action: str,
    *,
    answer: Optional[dict] = None,
    note: Optional[str] = None,
    reviewer: str = "console",
) -> LearningSample:
    """approve(정답 수정 가능) | reject | reset(→ pending)."""
    row = _get(db, sample_id)
    if action == "approve":
        _approve(row, answer, reviewer)
    elif action == "reject":
        row.status, row.split = "rejected", None
        row.reviewed_by, row.reviewed_at = reviewer, datetime.now(timezone.utc)
    elif action == "reset":
        row.status, row.split, row.reviewed_by, row.reviewed_at = "pending", None, None, None
    else:
        raise ReviewError(f"알 수 없는 action: {action}")
    if note is not None:
        row.note = note.strip() or None
    db.commit()
    return row


def bulk_review(db: Session, ids: Iterable[str], action: str, reviewer: str = "console") -> dict:
    """여러 건 승인·거절. 정답이 없어 승인할 수 없는 건은 건너뛴다."""
    done, skipped = 0, []
    for sample_id in ids:
        try:
            review(db, sample_id, action, reviewer=reviewer)
            done += 1
        except (LookupError, ReviewError) as exc:
            db.rollback()
            skipped.append({"id": sample_id, "reason": str(exc) or "없음"})
    return {"done": done, "skipped": skipped}


def _within(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    return any(resolved.is_relative_to(r.resolve()) for r in roots)


def resolve_file(rel: Optional[str], settings: Settings) -> Optional[Path]:
    """샘플의 상대 경로 → 실제 파일. 학습 데이터·업로드 폴더 밖이면 None (경로 조작 방지)."""
    if not rel:
        return None
    path = Path(rel)
    path = path if path.is_absolute() else settings.resolve_shared_path(rel)
    roots = (settings.feedback_path, settings.pseudo_label_path, settings.upload_path)
    return path if _within(path, roots) and path.is_file() else None


def delete_sample(db: Session, sample_id: str, settings: Settings | None = None) -> dict:
    """샘플 삭제 + 원본 파일 정리 (재동기화로 되살아나지 않게)."""
    settings = settings or get_settings()
    row = _get(db, sample_id)
    removed: list[str] = []
    others = (
        db.query(LearningSample)
        .filter(LearningSample.origin_id == row.origin_id, LearningSample.id != row.id)
        .filter(LearningSample.status != "deleted")
        .count()
    )
    if row.source != "request" and not others:
        # 원본 파일 (업로드 폴더의 작업 원본은 서비스 소유라 지우지 않는다)
        owned_roots = (settings.feedback_path, settings.pseudo_label_path)
        for rel in (row.label_path, row.image_path):
            path = resolve_file(rel, settings)
            if path is not None and _within(path, owned_roots):
                path.unlink(missing_ok=True)
                removed.append(path.name)
        fb = db.get(Feedback, row.origin_id)
        if fb is not None:
            db.delete(fb)
    row.status, row.split = "deleted", None
    row.prompt = row.answer = row.image_path = row.label_path = row.note = None
    row.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("학습 샘플 삭제 id={} origin={} files={}", sample_id, row.origin_id, removed)
    return {"id": sample_id, "removed_files": removed}


def approved_prompt_samples(db: Session, sources: Optional[Iterable[str]] = None) -> list[LearningSample]:
    """승인된 문장 샘플 (RAG·LoRA 입력)."""
    query = db.query(LearningSample).filter(
        LearningSample.kind == "prompt", LearningSample.status == "approved"
    )
    if sources is not None:
        query = query.filter(LearningSample.source.in_(list(sources)))
    return query.order_by(LearningSample.created_at.asc(), LearningSample.id).all()
