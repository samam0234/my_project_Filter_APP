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

# 세그 추론 런타임 (빌드 인자 SEG_RUNTIME)
#   ultralytics (기본): .pt 를 ultralytics + CPU 전용 torch 로 — 이미지 약 2.8 GB. YOLO_MODEL_PATH=models/yolo26m-seg.pt
#   onnx             : torch·ultralytics 없이 onnxruntime 만 (직접 구현 onnx_utils) — 훨씬 가벼움.
#                      YOLO_MODEL_PATH=models/yolo26m-seg.onnx 필요. 검증·크기: docs/plan/ONNX_INFERENCE.md
# 둘 다 없으면 세그가 가짜(stub) 마스크로 동작한다 (2026-10-06 Docker 재빌드 점검에서 발견).
# CI 는 가볍게 유지하려고 requirements.docker.txt 에 넣지 않고 이미지에서만 설치.
# ultralytics 가 끌고 오는 opencv-python 은 headless 와 cv2 가 겹치므로 지우고 headless 로 맞춘다.
# torch 휠 종류 (빌드 인자 TORCH_INDEX): cpu(기본) | cu128 (NVIDIA GPU 서버 — docker-compose.gpu.yml, 휠이 CUDA 런타임을 함께 가져온다)
ARG TORCH_INDEX=cpu
ARG SEG_RUNTIME=ultralytics
RUN if [ "$SEG_RUNTIME" = "ultralytics" ]; then       pip install --no-cache-dir --index-url https://download.pytorch.org/whl/${TORCH_INDEX} torch==2.11.0 torchvision       && pip install --no-cache-dir ultralytics==8.4.152       && pip uninstall -y opencv-python       && pip install --no-cache-dir --force-reinstall --no-deps opencv-python-headless==4.10.0.84;     elif [ "$SEG_RUNTIME" != "onnx" ]; then       echo "SEG_RUNTIME 은 ultralytics 또는 onnx" >&2 && exit 1;     fi

# LoRA 문장 해석 (빌드 인자 LLM_LORA=1, 선택) — LLM_PROVIDER=lora 또는 PROMPT_SECOND_OPINION 혼합에 필요한 transformers · peft.
# 기본 이미지에는 넣지 않는다 — CPU 에서는 실사용이 안 된다 (GPU 서버는 TORCH_INDEX=cu128 과 함께 — docker-compose.gpu.yml) (2026-10-09 측정: 첫 로드 699초, 문장당 평균 23초 · 최대 122초,
# Ollama 체인 약 7초). 이미지가 동작하는지 확인하거나 나중에 GPU 이미지로 바꿀 때를 위한 선택지다 (docs/guidance/llm-and-vision.md).
# 베이스 모델(Qwen2.5-1.5B-Instruct, HF 형식 폴더)은 backend/models/ 아래에 두고 LORA_BASE_MODEL=models/qwen2.5-1.5b-instruct
# SEG_RUNTIME=onnx 면 torch 가 없으므로 CPU torch 도 같이 넣는다.
ARG LLM_LORA=0
RUN if [ "$LLM_LORA" = "1" ]; then       python -c "import torch" 2>/dev/null || pip install --no-cache-dir --index-url https://download.pytorch.org/whl/${TORCH_INDEX} torch==2.11.0;       pip install --no-cache-dir transformers==5.17.0 peft==0.21.0 accelerate==1.15.0;     fi

# backend 앱 소스만 이미지에 포함 (WORKDIR=/app → app 패키지 경로 유지)
COPY backend/ ./

# 런타임 디렉터리 보장 (볼륨 마운트 전에도 동작)
RUN mkdir -p /app/data/uploads /app/data/feedback /app/data/pseudo_labels /app/logs /app/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
