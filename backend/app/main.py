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
    settings = get_settings()
    setup_logging(settings.debug)
    for path in (
        settings.upload_path,
        settings.feedback_path,
        settings.pseudo_label_path,
    ):
        ensure_dir(path)
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
    settings = get_settings()
    app = FastAPI(
        title="Cut & Keep",
        description="프롬프트 기반 선택적 배경 제거 필터 API",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
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


app = create_app()
