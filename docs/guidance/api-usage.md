# API Usage (요약)

Base: `http://localhost:8000` · Swagger: `/docs` · 상세: [`docs/API_DOCUMENTATION.md`](../API_DOCUMENTATION.md)

| Method | Path | 권한 | 설명 |
|--------|------|------|------|
| GET | `/health` | 공개 | 헬스 + db_dialect |
| POST | `/api/v1/auth/signup` · `login` · `logout` | 공개 | 계정 ([`auth.md`](./auth.md)) |
| GET | `/api/v1/auth/me` | 로그인 | 현재 사용자 |
| POST | `/api/v1/auth/find-id` · `password/request` · `password/reset` | 공개 | 아이디·비밀번호 찾기 |
| POST | `/api/v1/upload` | 공개 | file + prompt. 비로그인은 저장 없이 data URL 결과 (`saved=false`) |
| GET | `/api/v1/files/{id}/{before\|after}` | 로그인 · 본인 | 결과 파일 |
| GET | `/api/v1/jobs` · `/jobs/{id}` | 로그인 · 본인 | 내 작업 기록 |
| POST | `/api/v1/feedback` | 로그인 · 본인 | like/dislike (+ 정답 JSON) |
| POST · GET | `/api/v1/batch` · `/batch/{id}` | 로그인 · 본인 | Phase 2 stub |
| GET | `/api/v1/console/*` | 서버 PC 에서만 | 운영 콘솔 전체 조회 |
