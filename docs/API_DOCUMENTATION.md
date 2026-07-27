# API Documentation (draft)

Base URL: `http://localhost:8000`

## Health

`GET /health` → `{ "status": "ok", "version": "0.1.0", "phase": 1 }`

## Upload (Phase 1)

`POST /api/v1/upload`  
`multipart/form-data`: `file`, `prompt`

Response: `UploadResponse` — see `docs/plan/LOGIC_STRUCTURE.md` §6.

## Feedback

`POST /api/v1/feedback`  
JSON: `{ "job_id", "vote": "like"|"dislike", "comment?" }`

## Batch (Phase 2 scaffold)

`POST /api/v1/batch` · `GET /api/v1/batch/{job_id}`

Interactive docs: `/docs` (Swagger UI)
