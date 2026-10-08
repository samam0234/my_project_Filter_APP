"""서비스 DB(SQLite) 자동 백업.

2026-10-08 서비스 DB 가 깨져 작업 기록을 잃었다 (docs/plan/DATABASE.md "손상 복구") — 그때 백업이 없었다.
SQLite 온라인 백업 API(sqlite3.Connection.backup)는 서비스가 쓰는 중에도 일관된 사본을 만든다 (파일 복사는 쓰는 중이면 깨질 수 있음).

- 기동 직후 한 번 + DB_BACKUP_HOURS 마다 (services/maintenance): data/backups/{파일명}-YYYYmmdd-HHMMSS.db
- 최근 DB_BACKUP_KEEP 개만 남기고 오래된 것부터 지운다
- 백업본도 quick_check 로 확인 — 원본이 이미 깨졌으면 그 사실을 로그로 남기고 깨진 백업은 지운다 (좋은 백업을 밀어내지 않게)
학습 DB(MariaDB)는 컨테이너 볼륨이라 여기서 다루지 않는다 (mysqldump — docs/plan/DATABASE.md).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from loguru import logger

from app.core.config import Settings, get_settings


def backup_dir(settings: Settings) -> Path:
    return settings.resolve_runtime_path("data/backups")


def sqlite_file(settings: Settings) -> Path | None:
    """서비스 DB 가 SQLite 파일이면 그 경로, 아니면 None (MariaDB · DATABASE_URL 지정)."""
    if settings.database_url_override or (settings.db_dialect or "sqlite").strip().lower() not in {"sqlite", "local"}:
        return None
    return settings.resolve_runtime_path(settings.sqlite_path)


def backup_sqlite(src: Path, out_dir: Path, keep: int) -> Path | None:
    """src 의 일관된 사본을 out_dir 에 만들고 keep 개만 남긴다. 반환: 만든 백업 경로 (원본이 깨졌으면 None)."""
    if not src.is_file():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{src.stem}-{datetime.now():%Y%m%d-%H%M%S}.db"
    source = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(dst)
    try:
        source.backup(target)
        ok = target.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    except sqlite3.DatabaseError as exc:
        ok = False
        logger.error("서비스 DB 백업 실패 — 원본이 손상됐을 수 있음 ({}): {}", src, exc)
    finally:
        target.close()
        source.close()
    if not ok:
        dst.unlink(missing_ok=True)
        logger.error("서비스 DB 백업본이 정상이 아니라 지웠다 — 원본 점검 필요 ({})", src)
        return None
    olds = sorted(out_dir.glob(f"{src.stem}-*.db"))
    for old in olds[: max(0, len(olds) - keep)]:
        old.unlink(missing_ok=True)
    logger.info("서비스 DB 백업 {} (보관 {}개)", dst.name, min(len(olds), keep))
    return dst


def run_once(settings: Settings | None = None) -> Path | None:
    settings = settings or get_settings()
    src = sqlite_file(settings)
    if src is None:
        return None
    try:
        return backup_sqlite(src, backup_dir(settings), settings.db_backup_keep)
    except Exception:  # 백업 실패가 서비스를 멈추면 안 된다
        logger.exception("서비스 DB 백업 중 오류")
        return None
