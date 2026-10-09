# -*- coding: utf-8 -*-
"""접근 정책 테스트 — 비로그인은 처리·다운로드만, 저장·기록·피드백·배치는 로그인 회원 본인만.

파이프라인은 가짜로 바꿔(LLM·YOLO 없이) 결과 파일만 써 준다.
"""

from __future__ import annotations

import shutil
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("numpy")
pytest.importorskip("cv2")

import cv2
import numpy as np

from app.core.config import get_settings
from app.models.job import Job
from app.routers import upload as upload_router
from app.schemas.request import ParsedPrompt
from app.schemas.response import ProcessResult

PW = "cutkeep2026"


def _signup(client, username, email):
    r = client.post(
        "/api/v1/auth/signup",
        json={"username": username, "email": email, "password": PW, "agree_terms": True},
    )
    assert r.status_code == 201, r.text


def _jpeg() -> bytes:
    ok, buf = cv2.imencode(".jpg", np.full((32, 48, 3), 120, np.uint8))
    return buf.tobytes()


@pytest.fixture()
def env(api_env, monkeypatch):
    """업로드 파이프라인을 가짜로: backend/data/uploads/{zz…}/ 에 before/after 를 쓴다."""
    made: list[str] = []
    calls: list[dict] = []

    def fake_pipeline(image_bytes, prompt, job_id=None, persist=True):
        job_id = job_id or f"zztest{uuid4().hex[:20]}"
        made.append(job_id)
        calls.append({"persist": persist})
        out = get_settings().upload_path / job_id
        out.mkdir(parents=True, exist_ok=True)
        (out / "before.jpg").write_bytes(image_bytes)
        cv2.imwrite(str(out / "after.png"), np.zeros((32, 48, 4), np.uint8))
        return ProcessResult(
            job_id=job_id,
            status="ok",
            quality_score=0.9,
            message="ok",
            parsed_prompt=ParsedPrompt(target=["person"]),
            before_path=str(out / "before.jpg"),
            after_path=str(out / "after.png"),
        )

    monkeypatch.setattr(upload_router, "run_pipeline", fake_pipeline)
    api_env["made"] = made
    api_env["calls"] = calls
    yield api_env
    for job_id in made:
        shutil.rmtree(get_settings().upload_path / job_id, ignore_errors=True)


def _upload(client):
    return client.post(
        "/api/v1/upload",
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
        data={"prompt": "사람만 남기고 배경 제거"},
    )


# ------------------------------------------------------------------ 비로그인


def test_guest_upload_returns_download_only_and_stores_nothing(env):
    c = env["client"]
    r = _upload(c)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["saved"] is False
    assert body["after_url"].startswith("data:image/png;base64,")
    assert body["before_url"] is None
    assert env["calls"][-1]["persist"] is False  # 실패 케이스(학습 재료)도 남기지 않음
    assert not (get_settings().upload_path / body["job_id"]).exists()  # 디스크 산출물 삭제
    with env["Session"]() as db:
        assert db.query(Job).count() == 0  # DB 기록 없음


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/jobs"),
        ("get", "/api/v1/jobs/abc"),
        ("get", "/api/v1/batch/abc"),
    ],
)
def test_guest_is_blocked_from_history_and_batch(env, method, path):
    assert getattr(env["client"], method)(path).status_code == 401


def test_guest_cannot_feedback_or_batch(env):
    c = env["client"]
    assert c.post("/api/v1/feedback", json={"job_id": "x", "vote": "like"}).status_code == 401
    r = c.post(
        "/api/v1/batch",
        files=[("files", ("a.jpg", _jpeg(), "image/jpeg"))],
        data={"prompt": "사람만"},
    )
    assert r.status_code == 401


# ------------------------------------------------------------------ 로그인 회원


def test_member_upload_is_saved_and_listed(env):
    c = env["client"]
    _signup(c, "owner_01", "owner@example.com")
    r = _upload(c)
    body = r.json()
    assert body["saved"] is True
    assert body["after_url"] == f"/api/v1/files/{body['job_id']}/after"
    assert env["calls"][-1]["persist"] is True
    jobs = c.get("/api/v1/jobs").json()
    assert [j["job_id"] for j in jobs] == [body["job_id"]]
    assert c.get(f"/api/v1/jobs/{body['job_id']}").status_code == 200
    assert c.get(body["after_url"]).status_code == 200
    assert c.post("/api/v1/feedback", json={"job_id": body["job_id"], "vote": "like"}).status_code == 200


def test_other_member_and_guest_cannot_see_someone_elses_job(env):
    c = env["client"]
    _signup(c, "owner_01", "owner@example.com")
    job_id = _upload(c).json()["job_id"]

    c.post("/api/v1/auth/logout")
    # 비로그인: 파일도 404 (존재 여부를 알리지 않음)
    assert c.get(f"/api/v1/files/{job_id}/after").status_code == 404

    _signup(c, "other_01", "other@example.com")
    assert c.get("/api/v1/jobs").json() == []
    assert c.get(f"/api/v1/jobs/{job_id}").status_code == 404
    assert c.get(f"/api/v1/files/{job_id}/before").status_code == 404
    assert c.post("/api/v1/feedback", json={"job_id": job_id, "vote": "dislike"}).status_code == 404


def test_member_batch_is_private(env):
    c = env["client"]
    _signup(c, "owner_01", "owner@example.com")
    created = c.post(
        "/api/v1/batch",
        files=[("files", ("a.jpg", _jpeg(), "image/jpeg"))],
        data={"prompt": "사람만"},
    )
    assert created.status_code == 200, created.text
    batch_id = created.json()["job_id"]
    assert c.get(f"/api/v1/batch/{batch_id}").json()["status"] != "not_found"

    c.post("/api/v1/auth/logout")
    _signup(c, "other_01", "other@example.com")
    assert c.get(f"/api/v1/batch/{batch_id}").json()["status"] == "not_found"


# ------------------------------------------------------------------ 운영 콘솔


def test_console_api_is_local_only(env, monkeypatch):
    c = env["client"]  # TestClient 의 클라이언트 주소는 "testclient" (loopback 아님)
    assert c.get("/api/v1/console/jobs").status_code == 401
    monkeypatch.setattr(get_settings(), "console_allow_remote", True)
    assert c.get("/api/v1/console/jobs").status_code == 200


def test_console_admin_login_works_from_anywhere(env, monkeypatch):
    """원격(배포)에서는 CONSOLE_ADMINS 계정으로 로그인해야 콘솔 API 를 쓴다."""
    monkeypatch.setattr(get_settings(), "console_admins", "Boss_01, ops_02")
    c = env["client"]
    _signup(c, "member_01", "member@example.com")
    r = c.get("/api/v1/console/jobs")
    assert r.status_code == 403 and "관리자" in r.json()["detail"]  # 로그인했지만 관리자 아님
    c.post("/api/v1/auth/logout")
    _signup(c, "boss_01", "boss@example.com")  # 대소문자 무시
    assert c.get("/api/v1/console/jobs").status_code == 200
    assert c.get("/api/v1/console/me").json() == {"via": "admin", "username": "boss_01"}
    c.post("/api/v1/auth/logout")
    assert c.get("/api/v1/console/me").status_code == 401


def test_console_require_login_closes_loopback(env, monkeypatch):
    """리버스 프록시 뒤에서는 모든 요청이 127.0.0.1 로 보인다 → CONSOLE_REQUIRE_LOGIN=true 면 loopback 도 로그인 필수."""
    from app.core import access

    monkeypatch.setattr(access, "LOOPBACK", access.LOOPBACK | {"testclient"})  # 이 클라이언트를 서버 PC 로 취급
    c = env["client"]
    assert c.get("/api/v1/console/me").json() == {"via": "local", "username": None}
    monkeypatch.setattr(get_settings(), "console_require_login", True)
    assert c.get("/api/v1/console/me").status_code == 401
    monkeypatch.setattr(get_settings(), "console_admins", "boss_01")
    _signup(c, "boss_01", "boss@example.com")
    assert c.get("/api/v1/console/me").json()["via"] == "admin"


def test_preflight_warns_about_console_login():
    from app.core import preflight
    from app.core.config import Settings

    keys = lambda **v: {i.key for i in preflight.check(Settings.model_validate({"DB_DIALECT": "sqlite", **v}))}
    assert "CONSOLE_REQUIRE_LOGIN" in keys(CONSOLE_REQUIRE_LOGIN=False)
    assert "CONSOLE_ADMINS" in keys(CONSOLE_REQUIRE_LOGIN=True, CONSOLE_ADMINS="")  # .env 의 값과 무관하게
    assert not {"CONSOLE_REQUIRE_LOGIN", "CONSOLE_ADMINS"} & keys(CONSOLE_REQUIRE_LOGIN=True, CONSOLE_ADMINS="boss")


def test_console_file_links_bypass_owner_check_only_for_console(env, monkeypatch):
    c = env["client"]
    _signup(c, "owner_01", "owner@example.com")
    job_id = _upload(c).json()["job_id"]
    c.post("/api/v1/auth/logout")
    monkeypatch.setattr(get_settings(), "console_allow_remote", True)
    row = c.get(f"/api/v1/console/jobs/{job_id}").json()
    assert row["after_url"] == f"/api/v1/console/files/{job_id}/after"
    assert c.get(row["after_url"]).status_code == 200
    assert c.get(f"/api/v1/console/files/{job_id}/secret").status_code == 404
    assert c.get(f"/api/v1/files/{job_id}/after").status_code == 404  # 사용자 경로는 여전히 소유자만
