"""/api/v1 하위 API 라우터 집합."""

from fastapi import APIRouter

from app.core.constants import API_V1_PREFIX
from app.routers import batch, feedback, jobs, upload

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(upload.router)
api_router.include_router(feedback.router)
api_router.include_router(batch.router)
api_router.include_router(jobs.router)
