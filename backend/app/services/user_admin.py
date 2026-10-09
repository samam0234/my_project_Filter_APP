"""운영 콘솔 회원 관리 — 목록·잠금 해제·세션 끊기·계정 삭제.

삭제는 되돌릴 수 없다. 회원이 만든 것 중
  - 작업(jobs) · 배치(batch_jobs) · 영상 보관본 → 행과 파일 모두 삭제
  - 로그인 세션 · 재설정 코드 → 삭제
  - 학습 DB 샘플 → 계정 연결(user_id)만 끊는다. 검수된 문장은 RAG·LoRA 학습 데이터라 남기고,
    지울 것은 운영 콘솔 "학습 데이터" 화면에서 따로 삭제한다.
관리자(CONSOLE_ADMINS) 계정과 지금 로그인한 본인은 지울 수 없다 (콘솔에 아무도 못 들어가는 상황 방지).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.batch_job import BatchJob
from app.models.job import Job
from app.models.learning_sample import LearningSample
from app.models.user import AuthCode, AuthSession, User


class UserAdminError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


@dataclass
class UserRow:
    id: str
    username: str
    email: str
    display_name: Optional[str]
    created_at: Optional[str]
    last_login_at: Optional[str]
    locked: bool
    locked_until: Optional[str]
    failed_logins: int
    active_sessions: int
    job_count: int
    batch_count: int
    is_admin: bool


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite 는 tz 정보를 잃는다 — UTC 로 간주."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    dt = _aware(dt)
    return dt.isoformat() if dt else None


def _counts(db: Session, column, ids: list[str], *extra) -> dict[str, int]:
    """회원별 행 수 (한 번의 GROUP BY)."""
    if not ids:
        return {}
    rows = db.query(column, func.count()).filter(column.in_(ids), *extra).group_by(column).all()
    return {user_id: count for user_id, count in rows}


def list_users(
    db: Session,
    *,
    q: str = "",
    limit: int = 50,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[UserRow], int]:
    settings = settings or get_settings()
    query = db.query(User)
    term = q.strip().lower()
    if term:
        like = f"%{term}%"
        query = query.filter(or_(User.username.like(like), func.lower(User.email).like(like)))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    ids = [u.id for u in users]
    now = _now()
    jobs = _counts(db, Job.user_id, ids)
    batches = _counts(db, BatchJob.user_id, ids)
    sessions = _counts(db, AuthSession.user_id, ids, AuthSession.expires_at > now)
    admins = settings.console_admin_set
    rows = []
    for u in users:
        locked_until = _aware(u.locked_until)
        rows.append(
            UserRow(
                id=u.id,
                username=u.username,
                email=u.email,
                display_name=u.display_name,
                created_at=_iso(u.created_at),
                last_login_at=_iso(u.last_login_at),
                locked=bool(locked_until and locked_until > now),
                locked_until=_iso(locked_until),
                failed_logins=u.failed_logins or 0,
                active_sessions=sessions.get(u.id, 0),
                job_count=jobs.get(u.id, 0),
                batch_count=batches.get(u.id, 0),
                is_admin=u.username.lower() in admins,
            )
        )
    return rows, total


def _get(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserAdminError("회원을 찾을 수 없습니다.", status=404)
    return user


def unlock(db: Session, user_id: str) -> User:
    """로그인 실패 잠금 해제."""
    user = _get(db, user_id)
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    return user


def revoke_sessions(db: Session, user_id: str) -> int:
    """모든 기기에서 로그아웃 (세션 행 삭제 → 다음 요청부터 비로그인)."""
    _get(db, user_id)
    removed = db.query(AuthSession).filter(AuthSession.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return int(removed)


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _remove_dir(root: Path, path: Path) -> bool:
    if path.is_dir() and _inside(root, path) and path.resolve() != root.resolve():
        shutil.rmtree(path, ignore_errors=True)
        return True
    return False


def _owned_videos(upload_root: Path, user_id: str) -> list[Path]:
    """영상 보관본은 DB 행이 없고 owner.json 으로 소유자를 기록한다."""
    found = []
    for meta in (upload_root / "videos").glob("*/owner.json"):
        try:
            if json.loads(meta.read_text(encoding="utf-8")).get("user_id") == user_id:
                found.append(meta.parent)
        except (OSError, json.JSONDecodeError):
            continue
    return found


def delete_user(
    db: Session,
    ldb: Optional[Session],
    user_id: str,
    *,
    confirm: str,
    actor_username: Optional[str] = None,
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    user = _get(db, user_id)
    if confirm.strip().lower() != user.username:
        raise UserAdminError("확인용 아이디가 일치하지 않습니다.")
    if user.username.lower() in settings.console_admin_set:
        raise UserAdminError("관리자(CONSOLE_ADMINS) 계정은 지울 수 없습니다. 먼저 관리자 목록에서 빼 주세요.")
    if actor_username and actor_username.lower() == user.username:
        raise UserAdminError("지금 로그인한 계정은 지울 수 없습니다.")

    root = settings.upload_path
    jobs = db.query(Job).filter(Job.user_id == user_id).all()
    batches = db.query(BatchJob).filter(BatchJob.user_id == user_id).all()
    removed_dirs = 0
    for job in jobs:
        removed_dirs += _remove_dir(root, root / job.id)
        db.delete(job)
    for batch in batches:
        removed_dirs += _remove_dir(root, root / "batches" / batch.id)
        db.delete(batch)
    videos = _owned_videos(root, user_id)
    for folder in videos:
        removed_dirs += _remove_dir(root, folder)

    # SQLite 는 FK CASCADE 가 꺼져 있을 수 있어 직접 지운다
    db.query(AuthSession).filter(AuthSession.user_id == user_id).delete(synchronize_session=False)
    db.query(AuthCode).filter(AuthCode.user_id == user_id).delete(synchronize_session=False)
    username = user.username
    db.delete(user)
    db.commit()

    unlinked = 0
    if ldb is not None:
        unlinked = (
            ldb.query(LearningSample)
            .filter(LearningSample.user_id == user_id)
            .update({LearningSample.user_id: None}, synchronize_session=False)
        )
        ldb.commit()
    # 실패 · 확신 낮은 요청의 사진(피드백 폴더)도 지우고 남는 기록은 익명으로 (개인정보 처리방침 3절)
    from app.services.feedback_images import purge_user

    feedback = purge_user(None, user_id, ldb)

    logger.warning(
        "회원 삭제 user={} username={} by={} jobs={} batches={} videos={} learning_unlinked={}",
        user_id, username, actor_username or "console", len(jobs), len(batches), len(videos), unlinked,
    )
    return {
        "id": user_id,
        "username": username,
        "jobs": len(jobs),
        "batches": len(batches),
        "videos": len(videos),
        "removed_dirs": removed_dirs,
        "learning_unlinked": int(unlinked),
        "feedback_images_removed": feedback["removed_images"],
    }
