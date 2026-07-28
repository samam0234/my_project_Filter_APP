# Phase 1 MVP Checklist

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | Backend `/health` 200 | ☑ Docker 확인 | db_dialect 표시 |
| 2 | 단일 업로드 파이프라인 | ☐ | stub 가능 |
| 3 | Job DB 저장 | ☐ | `/api/v1/jobs` |
| 4 | Feedback 저장 | ☐ | DB + sidecar |
| 5 | Frontend 업로드 UI | ☐ | :5173 |
| 6 | Console Job 조회 | ☐ | :5174 |
| 7 | Docker cut_and_keep 스택 | ☑ | redis 6380 |
| 8 | 문서 허브 구조 | ☑ | docs/* |
| 9 | `pytest tests/structure` | ☐ | 폴더·plan md |
| 10 | `pytest tests/unit` | ☐ | backend 의존성 필요 |

상태 갱신 시 날짜를 이 파일 하단에 남긴다.  
테스트 전략: `docs/plan/TESTING.md`
