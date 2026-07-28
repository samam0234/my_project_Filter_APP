# 컷앤킵 (Cut & Keep)  
개발 · 실행 · 배포 가이드

**한 줄 설명**  
프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

이 문서는 1인 개발자가 **로컬 환경 세팅부터 Docker 배포까지** 바로 따라할 수 있도록 작성되었습니다.

---

## 1. 필수 환경 (Versions)

| 구분              | 버전                  | 비고                              |
|-------------------|-----------------------|-----------------------------------|
| Python            | **3.10 ~ 3.12**       | 3.11 권장                         |
| Node.js           | **18.x 또는 20.x**    | LTS 권장                          |
| npm / pnpm        | 최신                  | pnpm 권장                         |
| Docker            | 24+                   | Docker Compose v2 포함            |
| CUDA (선택)       | 11.8 / 12.x           | GPU 가속 시 필요                  |
| Git               | 2.30+                 | -                                 |

> **주의**  
> Python 3.13은 일부 패키지(Ultralytics, onnxruntime 등) 호환성 문제로 아직 권장하지 않습니다.

---

## 2. Backend 의존성 (Python)

### 2.1 핵심 패키지 (Phase 1 필수)

```txt
# requirements.txt (Phase 1 기준)

# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
pydantic==2.9.2
pydantic-settings==2.5.2

# Image Processing
opencv-python-headless==4.10.0.84
numpy==1.26.4
Pillow==10.4.0

# YOLO & ONNX
ultralytics==8.3.0
onnxruntime==1.19.2          # CPU
# onnxruntime-gpu==1.19.2    # GPU 사용 시

# LangGraph / LangChain
langchain==0.3.1
langchain-core==0.3.6
langgraph==0.2.28
langchain-openai==0.2.1      # 또는 langchain-community (로컬 LLM용)

# Utils
python-dotenv==1.0.1
aiofiles==24.1.0
loguru==0.7.2
```

### 2.2 Phase 2 추가 패키지

```txt
# Phase 2에서 추가

# 배치 처리
celery==5.4.0
redis==5.0.8

# Grounding DINO + SAM2 (필요 시)
# transformers==4.44.2
# torch==2.4.1
# torchvision==0.19.1
# segment-anything-2 관련 패키지 (설치 방법은 별도 스크립트 권장)

# LoRA / 학습 (주로 Colab에서 실행)
# peft==0.12.0
# accelerate==0.33.0
```

### 2.3 권장 설치 명령

```bash
# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 기본 설치
pip install --upgrade pip
pip install -r requirements.txt

# GPU 사용 시
# pip install onnxruntime-gpu==1.19.2
```

---

## 3. Frontend 의존성 (React)

### 3.1 핵심 패키지

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^4.5.5",
    "axios": "^1.7.7",
    "react-dropzone": "^14.2.3",
    "lucide-react": "^0.441.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.4",
    "vite": "^5.4.3",
    "tailwindcss": "^3.4.10",
    "postcss": "^8.4.45",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.9.1"
  }
}
```

### 3.2 설치 명령

```bash
cd frontend
npm install
# 또는
pnpm install
```

---

## 4. 프로젝트 초기 세팅 순서

```bash
# 1. 저장소 클론 또는 폴더 생성
git clone <your-repo> cut-and-keep
cd cut-and-keep

# 2. Backend 세팅 (의존성 파일은 저장소 루트)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 경량 Docker 와 동일: pip install -r requirements.docker.txt

# 3. Frontend 세팅
cd frontend
npm install

# 4. 환경변수 설정
cp .env.example .env
# .env 파일에 필요한 값 입력 (OPENAI_API_KEY, REDIS_URL 등)
```

### 3.9 테스트 (실행 전 검증)

```bash
# 저장소 루트
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
pytest
# 또는 골격만: pytest tests/structure
```

상세: `docs/plan/TESTING.md`, `tests/README.md`

### 4.1 주요 환경변수 (.env)

```env
# Backend
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# 파일 업로드 제한
MAX_UPLOAD_SIZE_MB=20
ALLOWED_MIME_TYPES=image/jpeg,image/png,image/webp

# 모델 경로 (YOLO26s instance segmentation — 기본 s 스케일)
YOLO_MODEL_PATH=models/yolo26s-seg.pt
# YOLO_MODEL_PATH=models/yolo26s-seg.onnx
UPLOAD_DIR=data/uploads
FEEDBACK_DIR=data/feedback

# LLM — 기본 로컬 Ollama E4B, 고도화 openai/gemini
# 상세: docs/plan/AI_MODEL_STRATEGY.md
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.0-flash

# Redis (Phase 2)
REDIS_URL=redis://localhost:6379/0

# 파일 자동 삭제 (시간)
FILE_RETENTION_HOURS=24

# Database — 로컬 SQLite / 배포 MariaDB
DB_DIALECT=sqlite
SQLITE_PATH=data/cutnkeep.db
# DB_DIALECT=mariadb
# MARIADB_HOST=localhost
# MARIADB_PORT=3306
# MARIADB_USER=cutnkeep
# MARIADB_PASSWORD=cutnkeep
# MARIADB_DATABASE=cutnkeep
# DATABASE_URL=mysql+pymysql://...
```

DB 설계·ERD·Repository 규칙은 `docs/plan/DATABASE.md` 참고.


---

## 5. 로컬 실행 가이드

### 5.1 Backend 실행

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 문서: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 5.2 Frontend 실행

```bash
cd frontend
npm run dev
```

- 기본 주소: http://localhost:5173

### 5.3 Celery Worker (Phase 2)

```bash
cd backend
celery -A app.tasks.batch_tasks worker --loglevel=info
```

### 5.4 Redis (Phase 2)

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

---

## 6. 주요 Import 예시 (Backend)

```python
# app/services/image_processor.py 예시

import cv2
import numpy as np
from ultralytics import YOLO
from onnxruntime import InferenceSession
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from loguru import logger

# OpenCV 전처리
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# YOLO
model = YOLO("models/yolov8n-seg.pt")  # 또는 ONNX

# LangGraph
from app.workflows.state import GraphState
from app.workflows.nodes import prompt_analyzer, segmentor, effect_applier
```

---

## 7. 배포 가이드 (Docker)

### 7.1 docker-compose.yml 예시

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    depends_on:
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  # Phase 2 Celery
  celery_worker:
    build:
      context: ./backend
    command: celery -A app.tasks.batch_tasks worker --loglevel=info
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    depends_on:
      - redis
      - backend
    restart: unless-stopped
```

### 7.2 Backend Dockerfile 예시

실제 파일: `backend/Dockerfile` (빌드 context = **저장소 루트**).

```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 루트 의존성 (경량 이미지 기본)
COPY requirements.docker.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

COPY backend/ ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 Frontend Dockerfile 예시 (Nginx)

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 7.4 배포 명령

```bash
# 전체 빌드 & 실행
docker compose up -d --build

# 로그 확인
docker compose logs -f backend

# 중지
docker compose down
```

---

## 8. 개발 시 필수 준수 사항 (요약)

1. Python **3.10~3.12**만 사용
2. 모든 OpenCV 단계에서 `.copy()` 사용
3. 배치 처리는 Generator 방식으로 메모리 관리
4. 실패 케이스는 무조건 `data/feedback/`에 저장
5. 업로드 파일은 24시간 후 자동 삭제
6. 설정값은 반드시 `core/config.py` + `.env`로 관리
7. Phase 1이 완전히 동작하기 전에 Phase 2 기능을 넣지 않음

---

## 9. 다음 단계 추천

1. 이 가이드대로 가상환경 + 패키지 설치
2. `backend/app` skeleton 코드 생성
3. `feature/opencv`부터 구현 시작
4. 로컬에서 단일 이미지 파이프라인 동작 확인 후 Docker 배포 진행

필요한 파일이 있으면 바로 말씀해주세요.  
(예: 실제 `requirements.txt`, `Dockerfile`, `.env.example` 등)
