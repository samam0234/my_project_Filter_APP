# Phase 1 MVP Checklist

**갱신:** 2026-07-28 · 스택: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | Backend `/health` 200 | ☑ | Docker · dialect=mysql 시 MariaDB |
| 2 | 단일 업로드 파이프라인 | ☐ | 가중치 없으면 stub 세그 |
| 3 | Job DB 저장 | ☐ | `/api/v1/jobs` · jobs 테이블 |
| 4 | Feedback 저장 | ☐ | DB + sidecar |
| 5 | Frontend 업로드 UI | ☐ | :5173 |
| 6 | Console Job 조회 | ☐ | :5174 · Compose 미포함 |
| 7 | Docker `cut_and_keep` 스택 | ☑ | redis 6380 · Adminer 8081 · MariaDB `MARIADB_PORT` |
| 8 | MariaDB 비밀번호 접속 | ☑ | GSS/SSL 없음 · DBeaver/Adminer |
| 9 | 문서 허브 · CURRENT_STACK | ☑ | docs/* |
| 10 | requirements 루트 | ☑ | backend/requirements 제거됨 |
| 11 | YOLO26s-seg 기본 문서 | ☑ | models/ 가중치는 수동 배치 |
| 12 | training/ 학습 구역 | ☑ | 가이드·스크립트 |
| 13 | `pytest tests/structure` | ☐ | 폴더·plan md |
| 14 | `pytest tests/unit` | ☐ | backend 의존성 필요 |
| 15 | 커밋 기록 branchs/commits | ☑ | 규칙 필수화 |

테스트 전략: `docs/plan/TESTING.md`
