"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.endpoints import batch, feedback, upload
from app.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(upload.router)
api_router.include_router(feedback.router)
api_router.include_router(batch.router)
