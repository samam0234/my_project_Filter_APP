# API Usage (요약)

Base: `http://localhost:8000` · Swagger: `/docs` · 상세: [`docs/API_DOCUMENTATION.md`](../API_DOCUMENTATION.md)

| Method | Path | 권한 | 설명 |
|--------|------|------|------|
| GET | `/health` | 공개 | 헬스 + db_dialect |
| POST | `/api/v1/auth/signup` · `login` · `logout` | 공개 | 계정 ([`auth.md`](./auth.md)) |
| GET | `/api/v1/auth/me` | 로그인 | 현재 사용자 |
| POST | `/api/v1/auth/find-id` · `password/request` · `password/reset` | 공개 | 아이디·비밀번호 찾기 |
| POST | `/api/v1/upload` | 공개 | 사진 file + prompt. 비로그인은 저장 없이 data URL 결과 (`saved=false`) |
| POST | `/api/v1/gif` | 공개 | 움직이는 GIF + prompt → 처리한 GIF (배경 제거면 `webp_url` 도). 비로그인은 data URL |
| POST · GET | `/api/v1/video` · `/video/{id}` | 공개 · 본인 | 영상 → mp4. 비로그인은 파일 응답(저장 없음), 회원은 보관 + 작업 기록 |
| GET | `/api/v1/files/{id}/{before\|after\|thumb\|webp}` | 로그인 · 본인 | 원본 · 결과 · 썸네일 · (GIF) WebP |
| GET | `/api/v1/jobs` · `/jobs/{id}` | 로그인 · 본인 | 내 작업 기록 — `kind` = image · video · gif |
| POST | `/api/v1/feedback` | 로그인 · 본인 | like/dislike (+ 정답 JSON) |
| POST · GET | `/api/v1/batch` · `/batch/{id}` | 로그인 · 본인 | 여러 장 처리 · 진행률 · zip |
| GET · POST | `/api/v1/console/*` | 관리자 로그인 또는 서버 PC | 운영 콘솔 (작업 · 학습 데이터 · 회원 · 시스템) |

비로그인 처리 요청은 IP 별 분당 `UPLOAD_RATE_GUEST_PER_MIN`, 회원은 계정별 `UPLOAD_RATE_MEMBER_PER_MIN` 까지.
