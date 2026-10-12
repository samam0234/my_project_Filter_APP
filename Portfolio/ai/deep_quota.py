"""안내 챗 깊이 추론 횟수.

한국 시간 날짜가 바뀌기 전에는 횟수를 줄이거나 지우지 않는다.
저장 파일은 안내 프로세스의 디스크라서, 사이트 함수가 다시 떠도 10으로 돌아가지 않는다.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

LIMIT = 10
RESETS = "한국 시간 오전 12시"
# 한국은 1988년 이후 서머타임이 없다. tzdata가 없는 Windows 안내 환경에서도 오전 12시를 같게 센다.
SEOUL = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "deep_quota.sqlite"
LEGACY = ROOT.parent / "site" / "data" / "deep_quota.sqlite"


def kst_date(now: datetime | None = None) -> str:
    moment = now or datetime.now(SEOUL)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=SEOUL)
    else:
        moment = moment.astimezone(SEOUL)
    return moment.strftime("%Y-%m-%d")


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.execute("PRAGMA synchronous=FULL")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS deep_day (
            kst_date TEXT PRIMARY KEY,
            used INTEGER NOT NULL
        )
        """
    )
    return db


def _import_legacy(db: sqlite3.Connection, legacy: Path) -> None:
    count = db.execute("SELECT COUNT(*) FROM deep_day").fetchone()[0]
    if count or not legacy.is_file():
        return
    old = sqlite3.connect(legacy)
    try:
        rows = old.execute(
            """
            SELECT kst_date, COUNT(*)
            FROM deep_uses
            WHERE status != 'refunded'
            GROUP BY kst_date
            """
        ).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        old.close()
    for date, used in rows:
        if not date or not used:
            continue
        db.execute(
            "INSERT INTO deep_day (kst_date, used) VALUES (?, ?)",
            (str(date), int(used)),
        )
    db.commit()


def _used(db: sqlite3.Connection, date: str) -> int:
    row = db.execute("SELECT used FROM deep_day WHERE kst_date = ?", (date,)).fetchone()
    return int(row[0]) if row else 0


def status(now: datetime | None = None, path: Path = STORE, legacy: Path = LEGACY) -> dict:
    date = kst_date(now)
    db = _connect(path)
    try:
        _import_legacy(db, legacy)
        used = _used(db, date)
    finally:
        db.close()
    return {
        "ok": True,
        "limit": LIMIT,
        "used": used,
        "remaining": max(0, LIMIT - used),
        "resets": RESETS,
        "date": date,
    }


def reserve(now: datetime | None = None, path: Path = STORE, legacy: Path = LEGACY) -> dict:
    """한 번을 더한다. 같은 날짜의 used 는 오르거나 그대로다. 실패해도 내리지 않는다."""
    date = kst_date(now)
    db = _connect(path)
    try:
        _import_legacy(db, legacy)
        db.execute("BEGIN IMMEDIATE")
        used = _used(db, date)
        if used >= LIMIT:
            db.execute("ROLLBACK")
            current = status(now, path, legacy)
            current["ok"] = False
            current["detail"] = "깊이 추론은 하루에 10번까지입니다. 한국 시간 오전 12시에 초기화됩니다."
            return current
        if used == 0:
            db.execute("INSERT INTO deep_day (kst_date, used) VALUES (?, 1)", (date,))
        else:
            db.execute("UPDATE deep_day SET used = ? WHERE kst_date = ?", (used + 1, date))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    finally:
        db.close()
    current = status(now, path, legacy)
    current["detail"] = ""
    return current
