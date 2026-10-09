# -*- coding: utf-8 -*-
"""실패 · 확신 낮은 요청 사진 보관 (services/feedback_images) — 보관 기간 정리 · 계정 삭제 때 정리.

학습 DB 는 메모리 SQLite 로만 (실제 DB 를 건드리지 않는다).
"""

from __future__ import annotations

import json
import os
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.learning import LearningBase
from app.models.feedback import Feedback
from app.services import feedback_images


@pytest.fixture()
def env(tmp_path, monkeypatch):
    settings = Settings.model_validate({"DB_DIALECT": "sqlite", "FEEDBACK_DIR": str(tmp_path / "feedback"),
                                        "FEEDBACK_IMAGE_RETENTION_DAYS": 30})
    folder = settings.feedback_path
    folder.mkdir(parents=True)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    LearningBase.metadata.create_all(engine)
    ldb = sessionmaker(bind=engine, expire_on_commit=False)()
    calls = []
    real = feedback_images._clear_db_paths
    # 세션 없이 부르면(주기 정리) 실제 학습 DB 를 열므로 테스트에서는 메모리 세션으로 돌린다
    monkeypatch.setattr(feedback_images, "_clear_db_paths",
                        lambda names, user_id=None, ldb_=None: calls.append((set(names), user_id)) or real(names, user_id, ldb_ or ldb))
    return settings, folder, ldb, calls


def _case(folder, case_id, user_id, age_days, ldb):
    img = folder / f"{case_id}.jpg"
    img.write_bytes(b"\xff\xd8photo")
    (folder / f"{case_id}.json").write_text(json.dumps({"case_id": case_id, "user_id": user_id, "image": img.name,
                                                       "prompt": "강아지만"}), encoding="utf-8")
    old = time.time() - age_days * 86400
    os.utime(img, (old, old))
    ldb.add(Feedback(id=case_id, job_id=case_id, user_id=user_id, vote="dislike", source="pipeline_failure",
                     image_path=f"data/feedback/{img.name}"))
    ldb.commit()
    return img


def test_expired_images_are_removed_but_records_stay(env):
    settings, folder, ldb, _ = env
    old = _case(folder, "old", "u1", 40, ldb)
    new = _case(folder, "new", "u1", 3, ldb)
    preview = feedback_images.purge_expired(settings, dry_run=True)
    assert preview["removed_files"] == 1 and old.exists()  # 미리 보기는 지우지 않는다
    out = feedback_images.purge_expired(settings)
    assert out["removed_files"] == 1 and not old.exists() and new.exists()
    side = json.loads((folder / "old.json").read_text(encoding="utf-8"))
    assert side["image"] is None and side["prompt"] == "강아지만"  # 요청 문장 기록은 남는다
    assert ldb.get(Feedback, "old").image_path is None and ldb.get(Feedback, "new").image_path


def test_account_deletion_removes_only_that_users_images(env):
    settings, folder, ldb, _ = env
    mine = _case(folder, "a", "u1", 1, ldb)
    other = _case(folder, "b", "u2", 1, ldb)
    out = feedback_images.purge_user(settings, "u1", ldb)
    assert out["removed_images"] == 1 and not mine.exists() and other.exists()
    side = json.loads((folder / "a.json").read_text(encoding="utf-8"))
    assert side["user_id"] is None and side["image"] is None  # 남는 기록은 익명
    row = ldb.get(Feedback, "a")
    ldb.refresh(row)
    assert row.user_id is None and row.image_path is None
    assert ldb.get(Feedback, "b").user_id == "u2"


def test_zero_days_keeps_no_images(env):
    settings, folder, ldb, _ = env
    img = _case(folder, "c", "u1", 0.001, ldb)
    feedback_images.purge_expired(settings.model_copy(update={"feedback_image_retention_days": 0}))
    assert not img.exists()
