# -*- coding: utf-8 -*-
"""서비스 DB / 학습 DB 분리 테스트.

- 피드백은 학습 DB(feedbacks · learning_samples)에, 서비스 DB 에는 jobs.feedback_saved 만
- 사이드카 파일 → 학습 DB 동기화 (멱등)
- MariaDB 가 꺼져 있으면 로컬 SQLite fallback (허용 시)
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("pydantic_settings")
pytest.importorskip("loguru")

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db import learning as learning_db
from app.db.learning import LearningBase
from app.models.feedback import Feedback
from app.models.job import Job
from app.models.learning_sample import LearningSample
from app.services.learning_catalog import assign_split, sync_from_files

CORRECTION = {"target": ["person"], "effect": "remove_object", "selector": {"position": "left", "rank": 2, "count": 1}}


def _learning_session():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    LearningBase.metadata.create_all(eng)
    return sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)


# ------------------------------------------------------------------ API → 학습 DB


@pytest.fixture()
def member(api_env, monkeypatch):
    """로그인 회원 + 저장된 job 1개 (파이프라인 없이 서비스 DB 에 직접)."""
    c = api_env["client"]
    r = c.post(
        "/api/v1/auth/signup",
        json={"username": "learner_01", "email": "learner@example.com", "password": "Passw0rd!x", "agree_terms": True},
    )
    assert r.status_code == 201, r.text
    user_id = r.json()["id"]
    with api_env["Session"]() as db:
        db.add(Job(id="job_l1", user_id=user_id, prompt="왼쪽에서 두 번째 사람 지워줘", status="ok",
                   parsed_prompt={"target": ["person"], "effect": "remove_bg"}))
        db.commit()
    api_env["user_id"] = user_id
    return api_env


def test_feedback_goes_to_learning_db_not_service_db(member):
    c = member["client"]
    r = c.post("/api/v1/feedback", json={"job_id": "job_l1", "vote": "like"})
    assert r.status_code == 200, r.text
    with member["LearningSession"]() as ldb:
        fb = ldb.query(Feedback).one()
        assert (fb.job_id, fb.user_id, fb.vote) == ("job_l1", member["user_id"], "like")
        assert fb.prompt == "왼쪽에서 두 번째 사람 지워줘"  # job 에서 보강
        sample = ldb.query(LearningSample).one()
        assert (sample.kind, sample.source, sample.status) == ("prompt", "like", "pending")
        assert sample.origin_id == fb.id and sample.answer["effect"] == "remove_bg"
        assert sample.label_path.endswith(f"{fb.id}.json")
    with member["Session"]() as db:
        assert db.get(Job, "job_l1").feedback_saved == 1
        # 서비스 DB 에는 피드백 테이블이 없다
        assert "feedbacks" not in inspect(db.get_bind()).get_table_names()


def test_dislike_with_answer_becomes_correction_sample(member):
    c = member["client"]
    r = c.post("/api/v1/feedback", json={"job_id": "job_l1", "vote": "dislike", "comment": json.dumps(CORRECTION)})
    assert r.status_code == 200
    with member["LearningSession"]() as ldb:
        sample = ldb.query(LearningSample).one()
        assert sample.source == "correction"
        assert sample.answer["effect"] == "remove_object" and sample.answer["selector"]["rank"] == 2


def test_learning_db_failure_keeps_sidecar(tmp_path):
    from app.services.feedback_service import FeedbackService

    class Broken:
        def get(self, *a, **k):
            raise RuntimeError("learning db down")

        def rollback(self):
            pass

    svc_eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from app.db.base import Base

    Base.metadata.create_all(svc_eng)
    settings = Settings.model_validate({"FEEDBACK_DIR": str(tmp_path / "fb")})
    with sessionmaker(bind=svc_eng)() as db:
        row, path = FeedbackService(db=db, settings=settings, learning_db=Broken()).save_case(
            job_id="j_x", vote="like", meta={"prompt": "사람만"}
        )
    assert row is None  # 학습 DB 실패
    assert path.is_file() and json.loads(path.read_text(encoding="utf-8"))["job_id"] == "j_x"  # 원본은 남음


# ------------------------------------------------------------------ 사이드카 동기화


def test_sync_from_files_is_idempotent(tmp_path):
    fb_dir, pl_dir = tmp_path / "feedback", tmp_path / "pseudo"
    fb_dir.mkdir()
    pl_dir.mkdir()
    (fb_dir / "j1_aaaa.json").write_text(json.dumps({
        "case_id": "j1_aaaa", "job_id": "j1", "vote": "dislike", "source": "user", "user_id": "u1",
        "comment": json.dumps(CORRECTION), "timestamp": "2026-10-01T00:00:00+00:00",
        "meta": {"prompt": "왼쪽 두 번째 사람 지워"},
    }), encoding="utf-8")
    (fb_dir / "j2_bbbb.jpg").write_bytes(b"jpg")
    (fb_dir / "j2_bbbb.json").write_text(json.dumps({
        "case_id": "j2_bbbb", "job_id": "j2", "vote": "dislike", "source": "pipeline_failure",
        "image": "j2_bbbb.jpg", "meta": {"prompt": "버스만", "parsed_prompt": {"target": ["bus"]}},
    }), encoding="utf-8")
    (fb_dir / "broken.json").write_text("{not json", encoding="utf-8")
    (pl_dir / "coco_1.json").write_text(json.dumps({
        "case_id": "coco_1", "prompt": "자동차만 크롭", "image": "1.jpg",
        "parsed_prompt": {"target": ["car"], "effect": "crop", "crop": True},
    }), encoding="utf-8")
    settings = Settings.model_validate({"FEEDBACK_DIR": str(fb_dir), "PSEUDO_LABEL_DIR": str(pl_dir)})

    Session = _learning_session()
    with Session() as ldb:
        assert sync_from_files(ldb, settings) == {"feedbacks": 2, "pseudo_labels": 1}
        assert sync_from_files(ldb, settings) == {"feedbacks": 0, "pseudo_labels": 0}  # 멱등
        by = {(s.kind, s.source): s for s in ldb.query(LearningSample).all()}
        assert set(by) == {("prompt", "correction"), ("segment", "pipeline_failure"), ("prompt", "pseudo_label")}
        assert by[("prompt", "correction")].user_id == "u1"
        assert by[("segment", "pipeline_failure")].image_path.endswith("j2_bbbb.jpg")
        assert by[("prompt", "pseudo_label")].image_path is None  # 실제 파일이 없으면 경로를 남기지 않음
        assert ldb.get(Feedback, "j1_aaaa").created_at.year == 2026


def test_assign_split_is_stable_and_mostly_train():
    ids = [f"{i:032x}" for i in range(1000)]
    splits = [assign_split(i) for i in ids]
    assert splits == [assign_split(i) for i in ids]
    assert 50 <= splits.count("val") <= 150


# ------------------------------------------------------------------ MariaDB fallback


@pytest.fixture()
def fresh_engine(monkeypatch):
    learning_db.reset_learning_engine()
    yield monkeypatch
    learning_db.reset_learning_engine()


def _unreachable(tmp_path, **extra):
    pytest.importorskip("pymysql")
    return Settings.model_validate({
        "LEARNING_DB_DIALECT": "mariadb", "MARIADB_HOST": "127.0.0.1", "MARIADB_PORT": 1,
        "LEARNING_DB_CONNECT_TIMEOUT": 1, "LEARNING_SQLITE_PATH": str(tmp_path / "learning.db"), **extra,
    })


def test_unreachable_mariadb_falls_back_to_sqlite(tmp_path, fresh_engine):
    fresh_engine.setattr(learning_db, "get_settings", lambda: _unreachable(tmp_path))
    assert learning_db.init_learning_db() == "sqlite(fallback)"
    assert (tmp_path / "learning.db").is_file()
    assert {"feedbacks", "learning_samples"} <= set(inspect(learning_db.get_learning_engine()).get_table_names())


def test_fallback_can_be_disabled(tmp_path, fresh_engine):
    fresh_engine.setattr(
        learning_db, "get_settings", lambda: _unreachable(tmp_path, LEARNING_DB_FALLBACK_SQLITE=False)
    )
    with pytest.raises(Exception):
        learning_db.init_learning_db()


def test_legacy_feedbacks_table_is_renamed(tmp_path, fresh_engine):
    """분리 전 스키마(jobs FK, prompt 없음)의 feedbacks 는 보존용 이름으로 바꾸고 새로 만든다."""
    from sqlalchemy import text

    db_file = tmp_path / "learning.db"
    eng = create_engine(f"sqlite:///{db_file.as_posix()}")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE feedbacks (id VARCHAR(64) PRIMARY KEY, job_id VARCHAR(64), vote VARCHAR(16))"))
        conn.execute(text("INSERT INTO feedbacks VALUES ('old1', 'j', 'like')"))
    eng.dispose()
    fresh_engine.setattr(
        learning_db, "get_settings",
        lambda: Settings.model_validate({"LEARNING_DB_DIALECT": "sqlite", "LEARNING_SQLITE_PATH": str(db_file)}),
    )
    learning_db.init_learning_db()
    insp = inspect(learning_db.get_learning_engine())
    assert "feedbacks_legacy" in insp.get_table_names()
    assert "prompt" in {c["name"] for c in insp.get_columns("feedbacks")}
