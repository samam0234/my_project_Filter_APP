# -*- coding: utf-8 -*-
"""운영 콘솔 시스템 화면 — 런타임 스냅샷 · 저장 공간 · 보관 기간 정리."""

from __future__ import annotations

import os
import time

import pytest

pytest.importorskip("fastapi")

from app.core.config import get_settings
from app.services.retention import cleanup_dir, storage_usage


def _file(path, size=10, age_hours=0.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    if age_hours:
        old = time.time() - age_hours * 3600
        os.utime(path, (old, old))
    return path


def test_cleanup_removes_only_expired_files(tmp_path):
    old = _file(tmp_path / "job1" / "after.png", 100, age_hours=30)
    _file(tmp_path / "job1" / "before.jpg", 50, age_hours=30)
    new = _file(tmp_path / "job2" / "after.png", 70)
    preview = cleanup_dir(tmp_path, 24, dry_run=True)
    assert (preview.removed_files, preview.freed_bytes, preview.dry_run) == (2, 150, True)
    assert old.exists()  # dry_run 은 지우지 않음
    done = cleanup_dir(tmp_path, 24)
    assert (done.removed_files, done.freed_bytes, done.removed_dirs) == (2, 150, 1)
    assert not (tmp_path / "job1").exists() and new.exists() and tmp_path.exists()


def test_storage_usage_splits_jobs_batches_videos(tmp_path):
    _file(tmp_path / "abc" / "after.png", 100, age_hours=48)
    _file(tmp_path / "batches" / "b1" / "out" / "0000.png", 30)
    _file(tmp_path / "videos" / "v1" / "result.webm", 7)
    areas = {a["name"]: a for a in storage_usage(tmp_path, 24)}
    assert (areas["jobs"]["files"], areas["jobs"]["bytes"], areas["jobs"]["expired_files"]) == (1, 100, 1)
    assert areas["jobs"]["oldest_hours"] >= 47.9
    assert (areas["batches"]["files"], areas["batches"]["bytes"]) == (1, 30)
    assert (areas["videos"]["files"], areas["videos"]["expired_files"]) == (1, 0)


@pytest.fixture()
def admin(api_env, monkeypatch):
    monkeypatch.setattr(get_settings(), "console_admins", "boss")
    c = api_env["client"]
    r = c.post("/api/v1/auth/signup", json={"username": "boss", "email": "boss@example.com", "password": "cutkeep2026"})
    assert r.status_code == 201
    return c


def test_system_snapshot_does_not_load_models(admin, monkeypatch):
    from app.services.segmentation import Segmentor
    from app.workflows import nodes

    monkeypatch.setattr(nodes, "_processor", None)

    def boom(*a, **k):
        raise AssertionError("시스템 화면이 세그 모델을 로드했다")

    monkeypatch.setattr(Segmentor, "__init__", boom)
    body = admin.get("/api/v1/console/system").json()
    assert body["segmentation"]["runtime"] == "not_loaded"
    assert body["video"]["output_format"] in {"mp4", "webm", "avi"} and body["video"]["ffmpeg"] is True
    assert body["console"]["admins"] == 1
    assert body["batch"]["redis_ok"] is None  # Celery 를 안 쓰면 Redis 를 확인하지 않음
    assert {a["name"] for a in body["storage"]["areas"]} == {"jobs", "batches", "videos"}
    assert any(i["key"] == "CONSOLE_REQUIRE_LOGIN" for i in body["preflight"])


def test_system_cleanup_dry_run_then_delete(admin):
    root = get_settings().upload_path
    stale = _file(root / "oldjob" / "after.png", 64, age_hours=get_settings().file_retention_hours + 1)
    fresh = _file(root / "newjob" / "after.png", 64)
    preview = admin.post("/api/v1/console/system/cleanup", params={"dry_run": True}).json()
    assert preview["removed_files"] == 1 and preview["dry_run"] is True and stale.exists()
    done = admin.post("/api/v1/console/system/cleanup").json()
    assert (done["removed_files"], done["freed_bytes"]) == (1, 64)
    assert not stale.exists() and fresh.exists()


def test_system_routes_require_console_access(api_env):
    c = api_env["client"]  # 원격 + 비로그인
    assert c.get("/api/v1/console/system").status_code == 401
    assert c.post("/api/v1/console/system/cleanup").status_code == 401
