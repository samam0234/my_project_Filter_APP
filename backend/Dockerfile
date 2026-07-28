# 컷앤킵 Backend 이미지 (FastAPI + OpenCV 런타임)
# Python 3.11 고정 (3.14 비권장 — 핀 패키지 호환)
#
# 빌드 컨텍스트: 저장소 루트 (docker-compose 의 context: .)
#   docker compose build backend
# 의존성 파일: 루트 requirements.docker.txt / requirements.txt

FROM python:3.11-slim

WORKDIR /app

# OpenCV(cv2) 가 필요로 하는 시스템 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 루트 의존성 설치 (경량 Docker 세트)
COPY requirements.docker.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# backend 앱 소스만 이미지에 포함 (WORKDIR=/app → app 패키지 경로 유지)
COPY backend/ ./

# 런타임 디렉터리 보장 (볼륨 마운트 전에도 동작)
RUN mkdir -p /app/data/uploads /app/data/feedback /app/data/pseudo_labels /app/logs /app/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
