"""백엔드가 스스로 도는 주기 작업 (기동 시 시작, 종료 시 멈춤).

- 서비스 DB 백업: DB_BACKUP_HOURS 마다 (services/db_backup) — SQLite 일 때만
- 업로드 정리: FILE_CLEANUP_MINUTES 마다 FILE_RETENTION_HOURS 가 지난 파일 삭제 (services/retention, 콘솔 "지금 정리"와 같은 함수)
  + 피드백 사진(실패 · 확신 낮음)은 FEEDBACK_IMAGE_RETENTION_DAYS 가 지나면 삭제 (services/feedback_images)
  + 이메일 인증을 마치지 않은 가입 신청(signup_pending)은 유효 시간이 지나면 삭제 (개인정보 처리방침 안내와 같게)
  예전에는 scripts/cleanup.py 를 누군가 돌려야 지워져 "24시간 보관" 안내가 지켜지지 않았다

여러 워커 프로세스로 띄워도 각 작업이 멱등이라 안전하다 (백업이 몇 개 더 생길 뿐 keep 개수로 정리됨).
"""

from __future__ import annotations

import threading
from typing import Callable

from loguru import logger

from app.core.config import Settings, get_settings

_STOP = threading.Event()
_THREADS: list[threading.Thread] = []


def cleanup_uploads(settings: Settings | None = None) -> dict:
    from app.services.retention import cleanup_dir

    settings = settings or get_settings()
    from app.services.feedback_images import purge_expired

    result = cleanup_dir(settings.upload_path, settings.file_retention_hours)
    if result.removed_files:
        logger.info(
            "보관 기간 지난 업로드 정리: 파일 {}개 ({:.1f}MB) · 빈 폴더 {}개",
            result.removed_files, result.freed_bytes / 1024 / 1024, result.removed_dirs,
        )
    # 실패 · 확신 낮은 요청의 사진(피드백 폴더)은 보관 기간이 따로다 (FEEDBACK_IMAGE_RETENTION_DAYS)
    return result.as_dict() | {"feedback_images": purge_expired(settings)}


def purge_signup_pending() -> int:
    """유효 시간(SIGNUP_CODE_TTL_MINUTES)이 지난 가입 신청을 지운다 — 이메일 · 비밀번호 해시를 필요 이상 두지 않는다."""
    from datetime import datetime, timezone

    from app.db.session import SessionLocal, get_engine
    from app.models.user import SignupPending

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        removed = (
            db.query(SignupPending)
            .filter(SignupPending.expires_at < datetime.now(timezone.utc))
            .delete(synchronize_session=False)
        )
        db.commit()
        if removed:
            logger.info("만료된 가입 신청 정리: {}건", removed)
        return int(removed)
    finally:
        db.close()


def _every(name: str, seconds: float, job: Callable[[], object]) -> threading.Thread:
    def loop() -> None:
        while not _STOP.is_set():
            try:
                job()
            except Exception:  # 주기 작업 실패가 서비스를 멈추면 안 된다
                logger.exception("주기 작업 실패: {}", name)
            if _STOP.wait(seconds):
                break

    thread = threading.Thread(target=loop, name=name, daemon=True)
    thread.start()
    return thread


def start(settings: Settings | None = None) -> list[str]:
    """켜진 주기 작업을 띄우고 그 이름 목록을 돌려준다."""
    from app.services import db_backup

    settings = settings or get_settings()
    if any(t.is_alive() for t in _THREADS):
        return [t.name for t in _THREADS]
    _STOP.clear()
    _THREADS.clear()
    if settings.db_backup_hours > 0 and db_backup.sqlite_file(settings) is not None:
        _THREADS.append(_every("db-backup", settings.db_backup_hours * 3600, lambda: db_backup.run_once(settings)))
    if settings.file_cleanup_minutes > 0:
        _THREADS.append(_every("upload-cleanup", settings.file_cleanup_minutes * 60, lambda: (cleanup_uploads(settings), purge_signup_pending())))
    names = [t.name for t in _THREADS]
    if names:
        logger.info("주기 작업 시작: {}", ", ".join(names))
    return names


def stop() -> None:
    _STOP.set()
