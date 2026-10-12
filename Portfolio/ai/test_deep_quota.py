"""깊이 추론 횟수는 한국 시간 날짜가 바뀌기 전에 10으로 돌아가지 않는다."""

import sqlite3
from datetime import datetime, timedelta, timezone

from deep_quota import reserve, status

SEOUL = timezone(timedelta(hours=9))


def test_same_kst_day_does_not_restore_and_next_midnight_does(tmp_path):
    store = tmp_path / "deep_quota.sqlite"
    legacy = tmp_path / "missing.sqlite"
    evening = datetime(2026, 10, 12, 23, 40, tzinfo=SEOUL)
    for _ in range(10):
        gate = reserve(evening, store, legacy)
        assert gate["ok"] is True
    blocked = reserve(evening, store, legacy)
    assert blocked["ok"] is False
    assert blocked["remaining"] == 0
    later = datetime(2026, 10, 12, 23, 59, tzinfo=SEOUL)
    again = status(later, store, legacy)
    assert again["date"] == "2026-10-12"
    assert again["used"] == 10
    assert again["remaining"] == 0
    after = datetime(2026, 10, 13, 0, 1, tzinfo=SEOUL)
    reset = status(after, store, legacy)
    assert reset["date"] == "2026-10-13"
    assert reset["remaining"] == 10
    db = sqlite3.connect(store)
    kept = db.execute("SELECT used FROM deep_day WHERE kst_date = '2026-10-12'").fetchone()
    db.close()
    assert kept[0] == 10


def test_utc_evening_is_still_the_same_kst_date(tmp_path):
    store = tmp_path / "deep_quota.sqlite"
    legacy = tmp_path / "missing.sqlite"
    before_midnight = datetime(2026, 10, 12, 14, 30, tzinfo=timezone.utc)
    reserve(before_midnight, store, legacy)
    assert status(before_midnight, store, legacy)["date"] == "2026-10-12"
    assert status(before_midnight, store, legacy)["used"] == 1


def test_legacy_site_rows_stay_spent(tmp_path):
    legacy = tmp_path / "site.sqlite"
    db = sqlite3.connect(legacy)
    db.execute("CREATE TABLE deep_uses (id INTEGER PRIMARY KEY, used_at TEXT, kst_date TEXT, status TEXT)")
    db.executemany(
        "INSERT INTO deep_uses (used_at, kst_date, status) VALUES ('t', '2026-10-12', ?)",
        [("refunded",), ("refunded",), ("done",), ("done",), ("reserved",)],
    )
    db.commit()
    db.close()
    store = tmp_path / "ai.sqlite"
    moment = datetime(2026, 10, 12, 21, 0, tzinfo=SEOUL)
    current = status(moment, store, legacy)
    assert current["used"] == 3
    assert current["remaining"] == 7
    reserve(moment, store, legacy)
    assert status(moment, store, legacy)["used"] == 4
