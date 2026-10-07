# -*- coding: utf-8 -*-
"""운영 콘솔 회원 관리 — 목록·잠금 해제·세션 끊기·계정 삭제(파일 포함)."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")

from app.core.config import get_settings
from app.models.batch_job import BatchJob
from app.models.job import Job
from app.models.learning_sample import LearningSample

PW = "cutkeep2026"


def _signup(c, name):
    r = c.post("/api/v1/auth/signup", json={"username": name, "email": f"{name}@example.com", "password": PW})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _login(c, name, password=PW):
    return c.post("/api/v1/auth/login", json={"username": name, "password": password})


@pytest.fixture()
def env(api_env, monkeypatch):
    monkeypatch.setattr(get_settings(), "console_admins", "boss")
    c = api_env["client"]
    _signup(c, "boss")  # 관리자로 로그인한 상태
    return api_env


def _users(c, **params):
    r = c.get("/api/v1/console/users", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _give_member_data(env, user_id):
    """회원 작업·배치·영상 보관본·학습 샘플을 파일과 함께 만든다."""
    root = get_settings().upload_path
    job_id, batch_id, video_id = (uuid4().hex for _ in range(3))
    (root / job_id).mkdir(parents=True)
    (root / job_id / "after.png").write_bytes(b"x")
    (root / "batches" / batch_id / "out").mkdir(parents=True)
    (root / "videos" / video_id).mkdir(parents=True)
    (root / "videos" / video_id / "owner.json").write_text(json.dumps({"user_id": user_id}), encoding="utf-8")
    with env["Session"]() as db:
        db.add(Job(id=job_id, user_id=user_id, prompt="p", status="ok"))
        db.add(BatchJob(id=batch_id, user_id=user_id, prompt="p", status="done", total=1))
        db.commit()
    with env["LearningSession"]() as ldb:
        ldb.add(LearningSample(id=uuid4().hex, kind="prompt", source="request", status="approved",
                               prompt="왼쪽 사람", user_id=user_id, origin_id=f"request:{uuid4().hex}"))
        ldb.commit()
    return root / job_id, root / "batches" / batch_id, root / "videos" / video_id


def test_list_users_with_counts_and_search(env):
    c = env["client"]
    member = _signup(c, "member_01")
    _give_member_data(env, member)
    _login(c, "boss")
    body = _users(c)
    assert body["total"] == 2
    row = next(u for u in body["items"] if u["username"] == "member_01")
    assert (row["job_count"], row["batch_count"], row["is_admin"]) == (1, 1, False)
    assert row["active_sessions"] == 1 and "password_hash" not in row
    assert next(u for u in body["items"] if u["username"] == "boss")["is_admin"] is True
    assert [u["username"] for u in _users(c, q="MEMBER")["items"]] == ["member_01"]  # 아이디·이메일 대소문자 무시


def test_unlock_locked_member(env, monkeypatch):
    c = env["client"]
    monkeypatch.setattr(get_settings(), "login_max_failures", 2)
    _signup(c, "member_02")
    c.post("/api/v1/auth/logout")
    for _ in range(2):
        _login(c, "member_02", "wrong-password")
    assert _login(c, "member_02").status_code == 429  # 잠김
    _login(c, "boss")
    row = next(u for u in _users(c)["items"] if u["username"] == "member_02")
    assert row["locked"] is True
    assert c.post(f"/api/v1/console/users/{row['id']}/unlock").json()["locked"] is False
    c.post("/api/v1/auth/logout")
    assert _login(c, "member_02").status_code == 200


def test_revoke_sessions_logs_member_out_everywhere(env, api_env):
    from fastapi.testclient import TestClient

    c = env["client"]
    member_client = TestClient(api_env["app"])
    member = _signup(member_client, "member_03")
    assert member_client.get("/api/v1/auth/me").status_code == 200
    r = c.post(f"/api/v1/console/users/{member}/sessions/revoke")
    assert r.json() == {"id": member, "revoked": 1}
    assert member_client.get("/api/v1/auth/me").status_code == 401


def test_delete_member_removes_rows_and_files(env):
    c = env["client"]
    member = _signup(c, "member_04")
    job_dir, batch_dir, video_dir = _give_member_data(env, member)
    _login(c, "boss")
    wrong = c.request("DELETE", f"/api/v1/console/users/{member}", json={"confirm": "member_4"})
    assert wrong.status_code == 400 and job_dir.exists()
    r = c.request("DELETE", f"/api/v1/console/users/{member}", json={"confirm": "MEMBER_04"})
    assert r.status_code == 200, r.text
    assert r.json() | {"id": None} == {"id": None, "username": "member_04", "jobs": 1, "batches": 1, "videos": 1,
                                         "removed_dirs": 3, "learning_unlinked": 1}
    assert not job_dir.exists() and not batch_dir.exists() and not video_dir.exists()
    with env["Session"]() as db:
        assert db.query(Job).count() == 0 and db.query(BatchJob).count() == 0
    with env["LearningSession"]() as ldb:
        sample = ldb.query(LearningSample).one()
        assert sample.user_id is None and sample.prompt == "왼쪽 사람"  # 검수 데이터는 남고 연결만 끊김
    assert _login(c, "member_04").status_code == 401
    assert c.request("DELETE", f"/api/v1/console/users/{member}", json={"confirm": "member_04"}).status_code == 404  # 이미 삭제됨


def test_cannot_delete_admin_or_self(env):
    c = env["client"]
    boss = next(u for u in _users(c)["items"] if u["username"] == "boss")
    r = c.request("DELETE", f"/api/v1/console/users/{boss['id']}", json={"confirm": "boss"})
    assert r.status_code == 400 and "관리자" in r.json()["detail"]
    assert c.request("DELETE", f"/api/v1/console/users/{uuid4().hex}", json={"confirm": "x"}).status_code == 404


def test_user_admin_requires_console_access(env):
    c = env["client"]
    c.post("/api/v1/auth/logout")
    _signup(c, "member_05")  # 관리자 아님
    assert c.get("/api/v1/console/users").status_code == 403
    assert c.post(f"/api/v1/console/users/{uuid4().hex}/unlock").status_code == 403
