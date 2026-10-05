# Data Flow

## 단일 업로드

```
User (frontend)
  → POST /api/v1/upload (file + prompt, 세션 쿠키 있으면 로그인)
  → security validate
  → run_pipeline(persist = 로그인 여부)   (LangGraph / linear fallback)
  ├─ 로그인:   JobRepository.save_result(user_id) → jobs table
  │            결과 파일 backend/data/uploads/{job_id}/ 보관
  │            UploadResponse(before/after 파일 URL, saved=true)
  └─ 비로그인: DB 저장 없음 · 실패 케이스 수집 없음
               after 를 data URL 로 담고 backend/data/uploads/{job_id}/ 즉시 삭제
               UploadResponse(after_url=data URL, before_url=null, saved=false)

로그인 회원만:
  → GET /api/v1/jobs · /jobs/{id} · /files/{id}/*   (본인 작업, 남의 것 404)
  → POST /api/v1/feedback                          → FeedbackRepository + data/feedback sidecar
  → POST/GET /api/v1/batch                         (본인 배치)
```

## 운영 콘솔 조회

```
Console (백엔드와 같은 PC)
  → GET /health
  → GET /api/v1/console/jobs          (loopback 만 허용, 전체 작업)
  → GET /api/v1/console/files/{id}/after
  → 대시보드 집계 (클라이언트 사이드)
```

## 파일 vs DB

| 데이터 | 위치 | 비로그인 |
|--------|------|----------|
| Job 메타 | 서비스 DB `jobs` (`user_id`) | 저장 안 함 |
| 이미지 before/after | `backend/data/uploads/{job_id}/` | 응답 후 즉시 삭제 |
| 피드백 이벤트 · 학습 데이터 목록 | 학습 DB (MariaDB) `feedbacks` · `learning_samples` — 경로·라벨만 | 없음 (피드백은 회원 전용) |
| 학습용 사이드카 | `data/feedback/*.json|.jpg` | 실패 케이스도 남기지 않음 |
| 계정 · 세션 · 재설정 코드 | 서비스 DB `users` · `auth_sessions` · `auth_codes` | — |
