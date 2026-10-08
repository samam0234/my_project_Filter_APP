"""백엔드가 스스로 도는 주기 작업 (기동 시 시작, 종료 시 멈춤).

- 서비스 DB 백업: DB_BACKUP_HOURS 마다 (services/db_backup) — SQLite 일 때만
- 업로드 정리: FILE_CLEANUP_MINUTES 마다 FILE_RETENTION_HOURS 가 지난 파일 삭제 (services/retention, 콘솔 "지금 정리"와 같은 함수)
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
    result = cleanup_dir(settings.upload_path, settings.file_retention_hours)
    if result.removed_files:
        logger.info(
            "보관 기간 지난 업로드 정리: 파일 {}개 ({:.1f}MB) · 빈 폴더 {}개",
            result.removed_files, result.freed_bytes / 1024 / 1024, result.removed_dirs,
        )
    return result.as_dict()


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
        _THREADS.append(_every("upload-cleanup", settings.file_cleanup_minutes * 60, lambda: cleanup_uploads(settings)))
    names = [t.name for t in _THREADS]
    if names:
        logger.info("주기 작업 시작: {}", ", ".join(names))
    return names


def stop() -> None:
    _STOP.set()
