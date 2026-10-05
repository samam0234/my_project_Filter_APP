# -*- coding: utf-8 -*-
"""unit 공용 fixture — 계정·접근 정책 API 테스트용 앱.

- 메모리 SQLite (StaticPool) 로 get_db · get_learning_db override — 실제 DB 를 건드리지 않음
- 메일은 가로채서 본문 확인 (auth_service.send_mail)
- lifespan(init_db)을 돌리지 않도록 TestClient 를 with 없이 사용
무거운 import 는 fixture 안에서만 해 의존성이 없는 환경의 다른 테스트 수집을 막지 않는다.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def api_env(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    pytest.importorskip("sqlalchemy")
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import app.models  # noqa: F401 — 테이블 메타데이터 등록
    from app.db.base import Base
    from app.db.learning import LearningBase, get_learning_db
    from app.db.session import get_db
    from app.main import create_app
    from app.services import auth_service

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    learning_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    LearningBase.metadata.create_all(learning_engine)
    LearningSession = sessionmaker(bind=learning_engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    def _learning_db():
        db = LearningSession()
        try:
            yield db
        finally:
            db.close()

    mails: list[dict] = []
    monkeypatch.setattr(
        auth_service,
        "send_mail",
        lambda to, subject, body, settings=None: mails.append({"to": to, "subject": subject, "body": body})
        or True,
    )
    # 피드백·의사 라벨 폴더를 임시 폴더로 — 실제 data/(학습·RAG 입력)를 오염시키지 않는다
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "feedback_dir", str(tmp_path / "feedback"))
    monkeypatch.setattr(get_settings(), "pseudo_label_dir", str(tmp_path / "pseudo_labels"))
    application = create_app()
    application.dependency_overrides[get_db] = _db
    application.dependency_overrides[get_learning_db] = _learning_db
    yield {
        "app": application,
        "client": TestClient(application),
        "Session": Session,
        "LearningSession": LearningSession,
        "mails": mails,
    }

