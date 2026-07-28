# Getting Started

루트 상세 가이드: **[RUN.md](../../RUN.md)** (서버 열기 · 포트 · Docker)

## 전제

- Python 3.10–3.12 (3.11 권장)
- Node 18/20
- (선택) Docker Desktop

## Backend

Python 의존성은 **저장소 루트** (`requirements.txt` / `requirements.docker.txt`).

```bash
# 저장소 루트에서
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 또는 경량: pip install -r requirements.docker.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

## User Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## Ops Console

```bash
cd console
npm install
npm run dev
# http://localhost:5174
```

## 환경변수

루트 `.env.example` 을 복사해 `.env` 를 만든다. 상세는 [RUN.md](../../RUN.md).
