"""/api/v1 하위 API 라우터 집합.

main.py 의 create_app 이 이 api_router 를 한 번에 include 한다.
개별 도메인(upload, feedback, batch, jobs)은 하위 모듈에 분리.
"""

from fastapi import APIRouter

from app.core.constants import API_V1_PREFIX
from app.routers import auth, batch, console, feedback, jobs, upload, video

# 공통 prefix: /api/v1
api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(auth.router)  # /auth/* 로그인·회원가입·계정 찾기
api_router.include_router(upload.router)  # POST /upload, GET /files/...
api_router.include_router(feedback.router)  # POST /feedback
api_router.include_router(batch.router)  # POST/GET /batch (회원 배치)
api_router.include_router(video.router)  # POST/GET /video (게스트는 저장 없음)
api_router.include_router(jobs.router)
api_router.include_router(console.router)  # /console/* 운영 콘솔 (이 PC 에서만)  # GET /jobs, /jobs/{id}
