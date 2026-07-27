# API Usage (요약)

Base: `http://localhost:8000`

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 + db_dialect |
| POST | `/api/v1/upload` | file + prompt |
| GET | `/api/v1/jobs` | Job 목록 |
| GET | `/api/v1/jobs/{id}` | Job 단건 |
| POST | `/api/v1/feedback` | like/dislike |
| POST | `/api/v1/batch` | Phase 2 stub |

Swagger: `/docs`  
상세: `docs/API_DOCUMENTATION.md`
