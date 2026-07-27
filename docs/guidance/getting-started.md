# Getting Started

## 전제

- Python 3.10–3.12 (3.11 권장)
- Node 18/20
- (선택) Docker Desktop

## Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 또는 경량: pip install -r requirements.docker.txt
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

루트 `.env.example` → `.env` 복사.  
로컬 DB 기본: `DB_DIALECT=sqlite`.
