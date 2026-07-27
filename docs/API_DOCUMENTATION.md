# API Documentation (draft)

Base URL: `http://localhost:8000`

## Health

`GET /health` → `{ "status": "ok", "version": "0.1.0", "phase": 1, "db_dialect": "sqlite" }`

## Upload (Phase 1)

`POST /api/v1/upload`  
`multipart/form-data`: `file`, `prompt`  
→ 파이프라인 실행 후 **DB `jobs` 테이블에 저장**

## Jobs

`GET /api/v1/jobs/{job_id}` — 단건 조회  
`GET /api/v1/jobs?limit=50` — 최근 목록

## Feedback

`POST /api/v1/feedback`  
JSON: `{ "job_id", "vote": "like"|"dislike", "comment?" }`  
→ **DB `feedbacks`** + `data/feedback/` 사이드카

## Batch (Phase 2 scaffold)

`POST /api/v1/batch` · `GET /api/v1/batch/{job_id}`  
→ **DB `batch_jobs`**

## DB

로컬 SQLite / 배포 MariaDB — `docs/plan/DATABASE.md`

Interactive docs: `/docs` (Swagger UI)

