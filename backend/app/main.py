"""FastAPI 진입점: lifespan, 미들웨어, 라우터."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app import __version__
from app.core.config import get_settings
from app.core.constants import PHASE
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
    setup_logging(settings.debug)
    # 런타임에 쓸 디렉터리가 없으면 만든다
    for path in (
        settings.upload_path,
        settings.feedback_path,
        settings.pseudo_label_path,
    ):
        ensure_dir(path)
    # SQLite/MariaDB 테이블 create_all (없으면 생성)
    init_db()
    logger.info(
        "컷앤킵 시작 env={} phase={} db={} upload={}",
        settings.app_env,
        PHASE,
        get_engine().dialect.name,
        settings.upload_path,
    )
    yield
    logger.info("컷앤킵 종료")


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
    )
    # /api/v1/* 엔드포인트 묶음
    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        """헬스체크: 프로세스 생존 + DB dialect 표시."""
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
        )

    return app


# uvicorn app.main:app 으로 로드되는 모듈 수준 앱 객체
app = create_app()
