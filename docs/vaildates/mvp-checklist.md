# Phase 1 MVP Checklist

**갱신:** 2026-09-30 · 스택: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | Backend `/health` 200 | ☑ | Docker · dialect=mysql 시 MariaDB |
| 2 | 단일 업로드 파이프라인 | ☑ | `backend/models/yolo26s-seg.pt` 실모델로 확인 (없으면 stub) |
| 3 | Job DB 저장 | ☑ | `/api/v1/jobs` · `backend/data/cutnkeep.db` |
| 4 | Feedback 저장 | ☑ | DB + `data/feedback/` sidecar |
| 5 | Frontend 사용자 앱 | ☑ | :5173 · 홈·작업실·작업 기록·상세·가이드·배치 6페이지 |
| 6 | Console Job 조회 | ☐ | :5174 · Compose 미포함 |
| 7 | Docker `cut_and_keep` 스택 | ☑ | redis 6380 · Adminer 8081 · MariaDB `MARIADB_PORT` |
| 8 | MariaDB 비밀번호 접속 | ☑ | GSS/SSL 없음 · DBeaver/Adminer |
| 9 | 문서 허브 · CURRENT_STACK | ☑ | docs/* |
| 10 | requirements 루트 | ☑ | backend/requirements 제거됨 |
| 11 | YOLO26s-seg 기본 문서 | ☑ | 서빙 `backend/models/` (`apply_best.py`) |
| 12 | training/ 학습 구역 | ☑ | 가이드·스크립트 |
| 13 | `pytest tests/structure` | ☑ | 폴더·plan md |
| 14 | `pytest tests/unit` | ☑ | 전체 132개 통과 (2026-09-30) |
| 15 | 커밋 기록 branchs/commits | ☑ | 규칙 필수화 |
| 16 | LLM 프롬프트 분석 | ☑ | Ollama gemma4:e4b 기본 · 실패 시 휴리스틱 |
| 17 | 특정 인스턴스 선택 · 물체 지우기 | ☑ | "맨 앞 빨간 안전모 남자만", "왼쪽에서 두 번째 사람 지워" |
| 18 | LoRA 프롬프트 어댑터 | ☑ | 평가 87.5% · `LLM_PROVIDER=lora` |
| 19 | 런타임 · 학습 폴더 분리 | ☑ | `backend/{data,models,logs}` · 루트 `data/feedback` |
| 20 | 로그인 · 회원가입 · 아이디/비밀번호 찾기 | ☑ | 배포 전 `SECRET_KEY` · `SMTP_*` · `SESSION_COOKIE_SECURE=true` 필수 |

테스트 전략: `docs/plan/TESTING.md`
