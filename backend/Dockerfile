# 컷앤킵 Backend 이미지 (FastAPI + OpenCV 런타임)
# Python 3.11 고정 (3.14 비권장 — 핀 패키지 호환)
#
# 빌드 컨텍스트: 저장소 루트 (docker-compose 의 context: .)
#   docker compose build backend
# 의존성 파일: 루트 requirements.docker.txt / requirements.txt

FROM python:3.11-slim

WORKDIR /app
# ultralytics 설정 폴더 (root 홈이 아닌 곳 — 기동 경고 방지)
ENV YOLO_CONFIG_DIR=/tmp/Ultralytics

# OpenCV(cv2) 가 필요로 하는 시스템 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 루트 의존성 설치 (경량 Docker 세트)
COPY requirements.docker.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# 세그 모델(.pt) 추론 — ultralytics + CPU 전용 torch (CUDA 판 대비 수 GB 작음)
# 없으면 세그가 가짜(stub) 마스크로 동작한다 (2026-10-06 Docker 재빌드 점검에서 발견).
# CI 는 가볍게 유지하려고 requirements.docker.txt 에 넣지 않고 이미지에서만 설치.
# ultralytics 가 끌고 오는 opencv-python 은 headless 와 cv2 가 겹치므로 지우고 headless 로 맞춘다.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.11.0 torchvision     && pip install --no-cache-dir ultralytics==8.4.152     && pip uninstall -y opencv-python     && pip install --no-cache-dir --force-reinstall --no-deps opencv-python-headless==4.10.0.84

# backend 앱 소스만 이미지에 포함 (WORKDIR=/app → app 패키지 경로 유지)
COPY backend/ ./

# 런타임 디렉터리 보장 (볼륨 마운트 전에도 동작)
RUN mkdir -p /app/data/uploads /app/data/feedback /app/data/pseudo_labels /app/logs /app/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
