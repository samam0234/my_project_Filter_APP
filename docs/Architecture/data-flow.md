# Data Flow

## 단일 업로드 (Phase 1)

```
User (frontend)
  → POST /api/v1/upload (file + prompt)
  → security validate
  → run_pipeline (LangGraph / linear fallback)
  → JobRepository.save_result → jobs table
  → UploadResponse (before/after URLs)

Optional:
  → POST /api/v1/feedback
  → FeedbackRepository + data/feedback sidecar
```

## 운영 콘솔 조회

```
Console
  → GET /health
  → GET /api/v1/jobs
  → 대시보드 집계 (클라이언트 사이드)
```

## 파일 vs DB

| 데이터 | 위치 |
|--------|------|
| Job 메타 | DB `jobs` |
| 이미지 before/after | `data/uploads/{job_id}/` |
| 피드백 메타 | DB `feedbacks` |
| 학습용 사이드카 | `data/feedback/*.json|.jpg` |
