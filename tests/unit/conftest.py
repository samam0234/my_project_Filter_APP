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

    import os

    # CNK_TEST_SERVICE_DB_URL 이 있으면 서비스 DB 를 그 DB(예: MariaDB 테스트 DB)로 — 운영과 같은 엔진에서 API 를 검증
    #   예) mysql+pymysql://user:pw@127.0.0.1:3309/cutnkeep_test?charset=utf8mb4   (매 테스트마다 테이블을 지우고 다시 만든다)
    service_url = os.environ.get("CNK_TEST_SERVICE_DB_URL")
    if service_url:
        engine = create_engine(service_url, pool_pre_ping=True)
        Base.metadata.drop_all(engine)
    else:
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
    # 업로드·배치·영상 파일도 임시 폴더로 — 실제 backend/data/uploads 에 테스트 찌꺼기를 남기지 않는다
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    # 라우터 밖에서 직접 세션을 여는 곳(배치 백그라운드 작업 · 파이프라인 실패 저장 · RAG · 기동 작업)도 테스트 DB 를 쓰게
    # — 엔진 싱글톤을 바꿔 둔다. 예전에는 이 경로들이 .env 의 실제 서비스 · 학습 DB 를 열었다
    # (실제 DB 에 테이블이 있으면 조용히 통과, 빈 CI 에서는 "no such table" — 2026-10-10 발견)
    import app.db.learning as learning_mod
    import app.db.session as session_mod

    monkeypatch.setattr(session_mod, "_engine", engine)
    monkeypatch.setattr(learning_mod, "_engine", learning_engine)
    monkeypatch.setattr(learning_mod, "_mode", "sqlite(test)")
    learning_mod.LearningSessionLocal.configure(bind=learning_engine)
    session_mod.SessionLocal.configure(bind=engine)
    from app.core.ratelimit import upload_limiter

    upload_limiter.reset()  # 테스트끼리 업로드 횟수가 섞이지 않게
    application = create_app()
    application.dependency_overrides[get_db] = _db
    application.dependency_overrides[get_learning_db] = _learning_db
    env = {
        "app": application,
        "client": TestClient(application),
        "Session": Session,
        "LearningSession": LearningSession,
        "mails": mails,
    }
    yield env
    engine.dispose()
    # 전역 세션 공장이 버린 테스트 엔진을 가리키지 않게 — 다음 실제 사용 때 get_engine() · get_learning_engine() 이 다시 묶는다
    session_mod.SessionLocal.configure(bind=None)
    learning_mod.LearningSessionLocal.configure(bind=None)

