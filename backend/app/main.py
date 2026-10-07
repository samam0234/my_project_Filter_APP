"""FastAPI 진입점: lifespan, 미들웨어, 라우터."""

from __future__ import annotations

import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app import __version__
from app.core.config import get_settings
from app.core import preflight
from app.core.constants import PHASE
from app.db.learning import init_learning_db, learning_db_mode, learning_session
from app.db.session import get_engine, init_db
from app.routers import api_router
from app.schemas.response import HealthResponse
from app.utils.image_utils import ensure_dir
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 기동/종료 시 한 번 실행되는 수명주기.

    - 기동: 로그 설정, 업로드·피드백 디렉터리 생성, DB 테이블 보장
    - 종료: 종료 로그만 남김 (추가 정리 로직은 이후 확장)
    """
    settings = get_settings()
    setup_logging(settings.debug, settings.log_path, settings.log_retention_days)
    _preflight(settings)
    # 런타임에 쓸 디렉터리가 없으면 만든다
    for path in (
        settings.upload_path,
        settings.feedback_path,
        settings.pseudo_label_path,
    ):
        ensure_dir(path)
    # 서비스 DB 테이블 create_all (없으면 생성)
    init_db()
    # 학습 DB (MariaDB, 꺼져 있으면 로컬 SQLite fallback) + 사이드카 파일 중 빠진 것 적재
    learning_mode = _init_learning(settings)
    logger.info(
        "컷앤킵 시작 env={} phase={} db={} learning_db={} upload={} model={} feedback={} logs={}",
        settings.app_env,
        PHASE,
        get_engine().dialect.name,
        learning_mode,
        settings.upload_path,
        settings.yolo_model_file,
        settings.feedback_path,
        settings.log_path,
    )
    if settings.preload_models:
        # 세그 모델(YOLO) 로드 + 첫 추론 초기화는 첫 요청에서 30초 이상 걸린다 → 기동 직후 백그라운드에서 미리.
        # 서버는 바로 요청을 받고, 로드가 끝나기 전 요청은 같은 싱글톤 생성을 기다린다.
        threading.Thread(target=_preload_models, name="preload-models", daemon=True).start()
    yield
    logger.info("컷앤킵 종료")


def _preflight(settings) -> None:
    """배포 설정 점검 — production 에서 위험한 기본값이면 기동 거부 (core/preflight)."""
    issues = preflight.check(settings)
    prod = preflight.is_production(settings)
    for issue in issues:
        log = logger.error if prod and issue.level == "error" else logger.warning
        log("설정 점검 [{}] {}: {}", issue.key, issue.level, issue.message)
    stop = preflight.blocking(settings, issues)
    if stop:
        raise RuntimeError(
            "production 설정 점검 실패: " + ", ".join(i.key for i in stop)
            + " (python -m app.core.preflight 로 확인, 급하면 PREFLIGHT_STRICT=false)"
        )


def _init_learning(settings) -> str:
    """학습 DB 준비. 실패해도 서비스는 뜬다 (피드백은 사이드카 파일로 남고 다음 기동 때 동기화)."""
    try:
        mode = init_learning_db()
        if settings.learning_sync_on_start:
            from app.services.learning_catalog import sync_from_files

            with learning_session() as ldb:
                sync_from_files(ldb, settings)
                if settings.learning_collect_requests:
                    from app.db.session import SessionLocal
                    from app.services.learning_catalog import sync_requests_from_jobs

                    with SessionLocal() as sdb:
                        sync_requests_from_jobs(ldb, sdb, settings)
        return mode
    except Exception as exc:
        logger.error("학습 DB 준비 실패 (피드백은 파일로만 저장): {}", exc)
        return "unavailable"


def _preload_models() -> None:
    try:
        from app.workflows import nodes

        started = time.perf_counter()
        processor = nodes._get_processor()
        # 모델 로드와 별개로 첫 추론에서 GPU/런타임 초기화가 10초 이상 걸린다 → 빈 이미지로 한 번 추론
        import numpy as np

        processor.segmentor.predict(np.zeros((640, 640, 3), np.uint8), targets=["person"])
        # OPEN_VOCAB_ENABLED 면 DINO·SAM2 도 — 안 하면 COCO 밖 대상의 첫 요청이 16초 걸린다
        from app.services.segmentation import warmup_open_vocab

        open_vocab = warmup_open_vocab()
        logger.info(
            "모델 미리 로드·워밍업 완료 {:.1f}s (오픈보캐브 {})",
            time.perf_counter() - started,
            "포함" if open_vocab else "제외",
        )
    except Exception as exc:  # 실패해도 첫 요청에서 다시 시도
        logger.warning("모델 미리 로드 실패 (첫 요청에서 다시 시도): {}", exc)


def create_app() -> FastAPI:
    """FastAPI 앱 인스턴스를 조립한다 (팩토리).

    CORS → API 라우터 → /health 순으로 붙인다.
    """
    settings = get_settings()
    app = FastAPI(
        title="Cut & Keep",
        description="프롬프트 기반 선택적 배경 제거 필터 API",
        version=__version__,
        lifespan=lifespan,
    )
    # 프론트(5173)·콘솔(5174) 등 허용 오리진
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # 다른 도메인의 프론트가 영상 응답의 안내 헤더를 읽을 수 있게
        expose_headers=["Content-Disposition", "X-Cutnkeep-Frames", "X-Cutnkeep-Held"],
    )
    @app.middleware("http")
    async def security_headers(request, call_next):
        """기본 보안 헤더 (API 응답이 다른 사이트 프레임·MIME 추측에 쓰이지 않게)."""
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if settings.session_cookie_secure:
            # HTTPS 배포일 때만 (로컬 http 에서 HSTS 를 박으면 브라우저가 계속 https 로 감)
            response.headers.setdefault("Strict-Transport-Security", "max-age=15552000")
        return response

    # /api/v1/* 엔드포인트 묶음
    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        """헬스체크: 프로세스 생존 + 서비스 DB dialect + 학습 DB 모드."""
        dialect = None
        try:
            dialect = get_engine().dialect.name
        except Exception:
            dialect = None
        return HealthResponse(
            status="ok",
            version=__version__,
            phase=PHASE,
            db_dialect=dialect,
            learning_db=learning_db_mode(),
        )

    return app


# uvicorn app.main:app 으로 로드되는 모듈 수준 앱 객체
app = create_app()
