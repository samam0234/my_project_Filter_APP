# -*- coding: utf-8 -*-
"""학습 데이터 검수 테스트 — 회원 요청 후보 수집 · 콘솔 승인/거절/정답 수정/일괄/삭제 · 재동기화 방지."""

from __future__ import annotations

import json
import shutil
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("cv2")

import cv2
import numpy as np

from app.core.config import get_settings
from app.models.feedback import Feedback
from app.models.learning_sample import LearningSample
from app.routers import upload as upload_router
from app.schemas.request import ParsedPrompt
from app.schemas.response import ProcessResult
from app.services.learning_catalog import sync_from_files, sync_requests_from_jobs

FIX = {"target": ["person"], "effect": "remove_object", "selector": {"position": "left", "rank": 2, "count": 1}}


@pytest.fixture()
def env(api_env, monkeypatch):
    made: list[str] = []

    def fake_pipeline(image_bytes, prompt, job_id=None, persist=True):
        job_id = job_id or f"zztest{uuid4().hex[:20]}"
        made.append(job_id)
        out = get_settings().upload_path / job_id
        out.mkdir(parents=True, exist_ok=True)
        (out / "before.jpg").write_bytes(image_bytes)
        cv2.imwrite(str(out / "after.png"), np.zeros((8, 8, 4), np.uint8))
        return ProcessResult(
            job_id=job_id, status="ok", quality_score=0.9, message="ok",
            parsed_prompt=ParsedPrompt(target=["person"], effect="remove_bg"),
            before_path=str(out / "before.jpg"), after_path=str(out / "after.png"),
        )

    monkeypatch.setattr(upload_router, "run_pipeline", fake_pipeline)
    monkeypatch.setattr(get_settings(), "console_allow_remote", True)
    c = api_env["client"]
    r = c.post("/api/v1/auth/signup", json={"username": "rev_01", "email": "rev@example.com", "password": "cutkeep2026"})
    assert r.status_code == 201
    api_env["user_id"] = r.json()["id"]
    yield api_env
    for job_id in made:
        shutil.rmtree(get_settings().upload_path / job_id, ignore_errors=True)


def _upload(c, prompt):
    ok, buf = cv2.imencode(".jpg", np.full((16, 16, 3), 90, np.uint8))
    r = c.post("/api/v1/upload", files={"file": ("a.jpg", buf.tobytes(), "image/jpeg")}, data={"prompt": prompt})
    assert r.status_code == 200, r.text
    return r.json()["job_id"]


def _samples(c, **params):
    r = c.get("/api/v1/console/learning/samples", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_member_request_becomes_pending_candidate_once(env):
    c = env["client"]
    job_id = _upload(c, "왼쪽에서 두 번째 사람 지워줘")
    _upload(c, "왼쪽에서 두 번째 사람 지워줘")  # 같은 문장은 후보 1건
    body = _samples(c, source="request")
    assert body["total"] == 1
    item = body["items"][0]
    assert (item["status"], item["job_id"], item["user_id"]) == ("pending", job_id, env["user_id"])
    assert item["answer"]["effect"] == "remove_bg"  # 시스템 해석 = 정답 후보
    assert item["has_image"] and c.get(item["image_url"]).status_code == 200


def test_guest_request_is_not_collected(env):
    c = env["client"]
    c.post("/api/v1/auth/logout")
    _upload(c, "사람만 남겨")
    with env["LearningSession"]() as ldb:
        assert ldb.query(LearningSample).count() == 0


def test_approve_with_edited_answer_assigns_split(env):
    c = env["client"]
    _upload(c, "왼쪽에서 두 번째 사람 지워줘")
    sid = _samples(c)["items"][0]["id"]
    bad = c.post(f"/api/v1/console/learning/samples/{sid}/review", json={"action": "approve", "answer": {"effect": "x"}})
    assert bad.status_code == 400
    r = c.post(f"/api/v1/console/learning/samples/{sid}/review", json={"action": "approve", "answer": FIX, "note": "지우기로 수정"})
    assert r.status_code == 200, r.text
    row = r.json()
    assert row["status"] == "approved" and row["split"] in {"train", "val"}
    assert row["answer"]["effect"] == "remove_object" and row["answer"]["selector"]["rank"] == 2
    stats = c.get("/api/v1/console/learning/stats").json()
    assert stats["by_status"] == {"approved": 1} and stats["by_source"]["request"] == {"approved": 1}


def test_bulk_review_skips_missing(env):
    c = env["client"]
    _upload(c, "사람만 남기고 배경 제거")
    _upload(c, "강아지만 남겨")
    ids = [i["id"] for i in _samples(c)["items"]]
    r = c.post("/api/v1/console/learning/samples/bulk", json={"ids": ids + ["nope"], "action": "reject"})
    assert r.json()["done"] == 2 and r.json()["skipped"][0]["id"] == "nope"
    assert _samples(c, status="rejected")["total"] == 2


def test_delete_removes_files_and_is_not_resurrected_by_sync(env):
    c = env["client"]
    job_id = _upload(c, "왼쪽에서 두 번째 사람 지워줘")
    assert c.post("/api/v1/feedback", json={"job_id": job_id, "vote": "dislike", "comment": json.dumps(FIX)}).status_code == 200
    correction = _samples(c, source="correction")["items"][0]
    sidecar = get_settings().feedback_path / f"{correction['origin_id']}.json"
    assert sidecar.is_file()

    r = c.delete(f"/api/v1/console/learning/samples/{correction['id']}")
    assert r.status_code == 200 and r.json()["removed_files"] == [sidecar.name]
    assert not sidecar.exists()
    assert _samples(c, source="correction")["total"] == 0
    assert c.delete(f"/api/v1/console/learning/samples/{correction['id']}").status_code == 404

    req = _samples(c, source="request")["items"][0]
    assert c.delete(f"/api/v1/console/learning/samples/{req['id']}").status_code == 200
    with env["LearningSession"]() as ldb, env["Session"]() as sdb:
        assert ldb.get(Feedback, correction["origin_id"]) is None
        # 재기동 동기화가 지운 것을 되살리지 않음 (요청 후보는 job 이 남아 있어도 삭제 표식으로 막힘)
        assert sync_from_files(ldb, get_settings()) == {"feedbacks": 0, "pseudo_labels": 0}
        assert sync_requests_from_jobs(ldb, sdb, get_settings()) == 0
        tomb = ldb.get(LearningSample, req["id"])
        assert tomb.status == "deleted" and tomb.prompt is None and tomb.answer is None


def test_broken_encoding_prompt_is_not_a_candidate(env):
    c = env["client"]
    _upload(c, "¹ö½º¸¸ ³²±â°í")
    assert _samples(c)["total"] == 0


def test_learning_console_is_local_only(env, monkeypatch):
    monkeypatch.setattr(get_settings(), "console_allow_remote", False)
    assert env["client"].get("/api/v1/console/learning/samples").status_code == 403
