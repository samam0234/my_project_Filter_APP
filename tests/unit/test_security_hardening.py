# -*- coding: utf-8 -*-
"""보안 강화: 압축 폭탄(사진·GIF·영상 해상도) · 프록시 뒤 클라이언트 IP · 서비스 DB 자동 백업 · 업로드 자동 정리."""

from __future__ import annotations

import io
import os
import sqlite3
import time

import pytest

pytest.importorskip("PIL")
pytest.importorskip("cv2")

import cv2
import numpy as np
from PIL import Image

from app.core.config import get_settings
from app.exceptions import FileValidationError


def _png(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    Image.new("L", (w, h)).save(buf, format="PNG", optimize=True)  # 단색 — 파일은 작고 풀면 크다
    return buf.getvalue()


# ---------- 압축 폭탄 ----------


def test_image_pixels_rejects_huge_but_small_file():
    from app.core.security import validate_image_pixels

    bomb = _png(8000, 8000)  # 64MP, 파일은 수십 KB
    assert len(bomb) < 200_000
    with pytest.raises(FileValidationError, match="해상도"):
        validate_image_pixels(bomb, max_pixels=40_000_000)
    assert validate_image_pixels(_png(640, 480), max_pixels=40_000_000) == (640, 480)


def test_upload_route_rejects_pixel_bomb(api_env, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_image_pixels", 1_000_000)
    r = api_env["client"].post(
        "/api/v1/upload", files={"file": ("big.png", _png(2000, 2000), "image/png")}, data={"prompt": "사람만 남기고 배경 제거"}
    )
    assert r.status_code == 400 and "해상도" in r.json()["detail"]


def test_gif_rejects_huge_frames():
    from app.services.gif_processor import read_gif

    buf = io.BytesIO()
    frames = [Image.new("P", (3000, 3000)) for _ in range(2)]
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:])
    with pytest.raises(ValueError, match="해상도"):
        read_gif(buf.getvalue(), max_frames=10, max_pixels=4_000_000)


def test_video_rejects_over_max_side(tmp_path):
    from app.schemas.request import ParsedPrompt
    from app.services.video_processor import process_video

    path = tmp_path / "wide.avi"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 5.0, (800, 64))
    for _ in range(2):
        w.write(np.zeros((64, 800, 3), np.uint8))
    w.release()

    class Never:
        def predict(self, *a, **k):
            raise AssertionError("해상도 검사 전에 세그를 돌리면 안 된다")

    with pytest.raises(ValueError, match="해상도"):
        process_video(path, tmp_path / "out", ParsedPrompt(target=["person"]), Never(), max_side=640)


# ---------- 프록시 뒤 클라이언트 IP ----------


class _Req:
    def __init__(self, host, real=None):
        self.client = type("C", (), {"host": host})()
        self.headers = {"x-real-ip": real} if real else {}


def test_client_ip_trusts_real_ip_only_from_proxy_range():
    from app.core.ratelimit import client_ip

    nets = "172.16.0.0/12"
    assert client_ip(_Req("172.18.0.5", "203.0.113.7"), nets) == "203.0.113.7"  # nginx 컨테이너 → 실제 IP
    assert client_ip(_Req("203.0.113.9", "127.0.0.1"), nets) == "203.0.113.9"  # 밖에서 보낸 헤더는 무시
    assert client_ip(_Req("172.18.0.5", "not-an-ip"), nets) == "172.18.0.5"
    assert client_ip(_Req("172.18.0.5", "203.0.113.7"), "") == "172.18.0.5"  # 설정이 없으면 연결 주소


def test_guests_behind_proxy_get_separate_limits(api_env, monkeypatch):
    """nginx 뒤에서도 비로그인 업로드 한도가 사람(IP)마다 따로 — 예전에는 전원이 한 한도를 나눠 썼다."""
    import asyncio

    import httpx

    settings = get_settings()
    monkeypatch.setattr(settings, "trusted_proxies", "172.16.0.0/12")
    monkeypatch.setattr(settings, "upload_rate_guest_per_min", 1)
    bad = {"file": ("x.txt", b"nope", "text/plain")}  # 검증에서 400 — 한도만 소모

    async def run():
        # 연결 주소 = nginx 컨테이너(172.18.0.5), 실제 사용자는 X-Real-IP
        transport = httpx.ASGITransport(app=api_env["app"], client=("172.18.0.5", 50000))
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            post = lambda ip: c.post("/api/v1/upload", files=bad, data={"prompt": "p"}, headers={"X-Real-IP": ip})  # noqa: E731
            return [(await post("198.51.100.1")).status_code, (await post("198.51.100.1")).status_code,
                    (await post("198.51.100.2")).status_code]

    assert asyncio.run(run()) == [400, 429, 400]


def test_console_local_check_ignores_forwarded_headers(api_env, monkeypatch):
    """콘솔 "이 PC" 허용은 연결 주소로만 — X-Real-IP: 127.0.0.1 로 들어올 수 없다."""
    settings = get_settings()
    monkeypatch.setattr(settings, "trusted_proxies", "0.0.0.0/0")
    monkeypatch.setattr(settings, "console_allow_remote", False)
    monkeypatch.setattr(settings, "console_require_login", False)
    r = api_env["client"].get("/api/v1/console/me", headers={"X-Real-IP": "127.0.0.1", "X-Forwarded-For": "127.0.0.1"})
    assert r.status_code == 401  # TestClient 연결 주소("testclient")는 loopback 이 아님


# ---------- 서비스 DB 백업 ----------


def _make_db(path):
    con = sqlite3.connect(path)
    con.execute("create table t (x int)")
    con.executemany("insert into t values (?)", [(i,) for i in range(500)])
    con.commit()
    con.close()


def test_backup_sqlite_copies_and_keeps_latest(tmp_path):
    from app.services.db_backup import backup_sqlite

    src = tmp_path / "cutnkeep.db"
    _make_db(src)
    out = tmp_path / "backups"
    made = []
    for i in range(4):
        old = out / f"cutnkeep-2026010{i}-000000.db"
        out.mkdir(exist_ok=True)
        old.write_bytes(src.read_bytes())
        made.append(old)
    dst = backup_sqlite(src, out, keep=3)
    assert dst is not None and dst.is_file()
    assert sqlite3.connect(dst).execute("select count(*) from t").fetchone()[0] == 500
    left = sorted(p.name for p in out.glob("cutnkeep-*.db"))
    assert len(left) == 3 and dst.name in left  # 가장 오래된 것부터 지움
    assert not made[0].exists()


def test_backup_of_corrupt_db_is_discarded(tmp_path):
    from app.services.db_backup import backup_sqlite

    src = tmp_path / "cutnkeep.db"
    _make_db(src)
    data = bytearray(src.read_bytes())
    data[4096 : 4096 * 2] = b"[ WARN] garbage " * 256
    src.write_bytes(bytes(data))
    out = tmp_path / "backups"
    good = out / "cutnkeep-20260101-000000.db"
    out.mkdir()
    good.write_bytes(b"previous good backup")
    assert backup_sqlite(src, out, keep=1) is None
    assert good.exists()  # 깨진 백업이 좋은 백업을 밀어내지 않는다
    assert [p.name for p in out.iterdir()] == [good.name]


def test_sqlite_file_none_for_mariadb():
    from app.core.config import Settings
    from app.services.db_backup import sqlite_file

    assert sqlite_file(Settings.model_validate({"DB_DIALECT": "mariadb"})) is None
    assert sqlite_file(Settings.model_validate({"DB_DIALECT": "sqlite", "SQLITE_PATH": "data/x.db"})).name == "x.db"


# ---------- 업로드 자동 정리 ----------


def test_cleanup_uploads_removes_only_expired(tmp_path, monkeypatch):
    from app.services import maintenance

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "file_retention_hours", 24)
    old = settings.upload_path / "job_old" / "after.png"
    new = settings.upload_path / "job_new" / "after.png"
    for p in (old, new):
        p.parent.mkdir(parents=True)
        p.write_bytes(b"x")
    stamp = time.time() - 25 * 3600
    os.utime(old, (stamp, stamp))
    result = maintenance.cleanup_uploads(settings)
    assert result["removed_files"] == 1 and not old.exists() and new.exists()
    assert not old.parent.exists()  # 빈 폴더도 정리


def test_cleanup_keeps_placeholder_files(tmp_path):
    """자동 정리가 저장소의 .gitkeep 을 지우면 git 에 삭제로 잡힌다 — 숨김 파일은 건드리지 않는다."""
    from app.services.retention import cleanup_dir

    keep = tmp_path / ".gitkeep"
    keep.write_text("")
    stamp = time.time() - 48 * 3600
    os.utime(keep, (stamp, stamp))
    assert cleanup_dir(tmp_path, 24).removed_files == 0 and keep.exists()


def test_maintenance_starts_enabled_jobs_only(monkeypatch, tmp_path):
    from app.services import maintenance

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "db_backup_hours", 0)
    monkeypatch.setattr(settings, "file_cleanup_minutes", 60)
    maintenance.stop()
    for t in maintenance._THREADS:
        t.join(timeout=5)
    try:
        assert maintenance.start(settings) == ["upload-cleanup"]
    finally:
        maintenance.stop()
        for t in maintenance._THREADS:
            t.join(timeout=5)


def test_backup_writes_part_then_renames_and_cleans_stale(tmp_path):
    """백업 도중 끊겨도 반쪽 파일이 목록에 섞이지 않고, 오래된 조각은 다음 백업 때 지운다."""
    from app.services.db_backup import backup_sqlite

    src = tmp_path / "cutnkeep.db"
    _make_db(src)
    out = tmp_path / "backups"
    out.mkdir()
    stale = out / "cutnkeep-20260101-000000.db-journal"
    stale.write_bytes(b"x")
    old = time.time() - 2 * 3600
    os.utime(stale, (old, old))
    dst = backup_sqlite(src, out, keep=3)
    assert dst is not None and dst.suffix == ".db"
    assert not stale.exists()
    assert not list(out.glob("*.part*"))
