# Getting Started

루트 상세 가이드: **[RUN.md](../../RUN.md)**  
현재 포트·DB·Docker: **[CURRENT_STACK.md](../plan/CURRENT_STACK.md)**

## 전제

- Python 3.10–3.12 (3.11 권장, 3.14 비권장)
- Node 18/20
- (선택) Docker Desktop · 로컬 Ollama `gemma4:e4b`
- (선택) `models/yolo26s-seg.pt` — 없으면 stub 세그

## Backend

Python 의존성은 **저장소 루트** (`requirements.txt` / `requirements.docker.txt`).  
`backend/requirements*.txt` 는 **없음** (루트로 이전됨).

```bash
# 저장소 루트에서
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

## User Frontend

```bash
cd frontend && npm install && npm run dev
# http://localhost:5173
```

## Ops Console

```bash
cd console && npm install && npm run dev
# http://localhost:5174 — Compose 미포함
```

## Docker 한 번에

```bash
docker compose -p cut_and_keep --env-file .env up -d --build
# Adminer :8081 · MariaDB 호스트 포트 = MARIADB_PORT · Redis :6380
```

## 환경변수

루트 `.env.example` → `.env`.  
로컬 DB 기본 sqlite · Docker backend 는 mariadb. 상세: [RUN.md](../../RUN.md), [DATABASE.md](../plan/DATABASE.md).
