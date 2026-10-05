# 서비스 DB와 학습 데이터 DB 분리 / `c3799bf8cfc03e04af2f97a9731d53f582901a5f`

> 브랜치: `feature/db-split`  
> 작성일: `2026-10-06 03:03`  
> 작성자: `agent`  
> 파일명: `261006_0303_c3799bf_db-split-service-learning_feature-db-split.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(db): 서비스 DB와 학습 데이터 DB 분리` |
| **커밋 번호 (SHA)** | `c3799bf8cfc03e04af2f97a9731d53f582901a5f` |
| **짧은 SHA** | `c3799bf` |
| **브랜치** | `feature/db-split` |
| **부모 커밋** | `b5d3430` (feature/rag) |

## 2. 주 커밋 내용

- 서비스 DB(SQLite): `users` · `auth_*` · `jobs` · `batch_jobs`
- 학습 DB(MariaDB): `feedbacks` · 신규 `learning_samples` (학습 데이터 카탈로그 — 경로·정답·출처·검수 상태·split)
- 기동 시 사이드카 파일 → 학습 DB 동기화, MariaDB 미접속 시 SQLite fallback

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 결정: 간단한 서비스·유저 데이터는 SQLite, 학습을 위한 데이터 **기록**(이미지 자체가 아님)은 MariaDB.
이어지는 피드백 검수(승인·삭제)·사용자 프롬프트 학습의 기반 테이블이 필요했다.

### 3.2 변경 범위

- 추가: `backend/app/db/learning.py`, `backend/app/models/{learning,learning_sample}.py`,
  `backend/app/services/learning_catalog.py`, `tests/unit/test_learning_db.py`
- 수정: `backend/app/{core/config.py, db/base.py, main.py, models/{__init__,feedback,job}.py,
  repositories/{feedback,job}_repository.py, routers/feedback.py, schemas/response.py, services/feedback_service.py}`,
  `docker-compose.yml`, `.env.example`, `tests/unit/conftest.py`,
  `docs/plan/{DATABASE,CURRENT_STACK}.md`, `docs/Architecture/{docker-topology,data-flow}.md`

### 3.3 기술 포인트

- `LearningBase` 로 메타데이터를 분리해 각 DB 에 자기 테이블만 생성. 두 DB 사이 FK 없음 (job_id·user_id 값 참조)
- 두 DB 트랜잭션이 없으므로 저장 순서: 사이드카(원본) → 학습 DB → `jobs.feedback_saved`. 학습 DB 실패는 다음 기동 동기화로 복구
- `learning_samples` 는 (origin_id, kind) 유일 → 동기화 멱등. split 은 id 해시로 고정 (10% val)
- 경로는 저장소 루트 기준 상대 경로 (호스트·Docker 같은 값)
- 분리 전 스키마 `feedbacks`(jobs FK)가 MariaDB 에 있으면 `feedbacks_legacy` 로 이름을 바꿔 보존
- **테스트 오염 발견·수정**: `test_access` 가 실제 `data/feedback` 에 like 사이드카를 남기고 있었다 (zztest 12건).
  지난 RAG 평가의 "실제 피드백 1건"("사람만 남기고 배경 제거")도 이 찌꺼기였음 → fixture 가 임시 폴더 사용, 파일 삭제

### 3.4 의도적으로 하지 않은 것

- 기존 서비스 SQLite 의 `feedbacks` 테이블 삭제 (보존, 더 이상 사용 안 함)
- Alembic 도입
- RAG 를 학습 DB 기반으로 전환 (다음 브랜치 `feature/feedback-review`)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 실서버(호스트 uvicorn + Docker MariaDB 3309): `/health` → `db_dialect: sqlite`, `learning_db: mysql`
- [x] 첫 기동 동기화: 피드백 3건 · 의사 라벨 5000건 적재 (약 7 s), 두 번째 기동은 추가 0건 (1 s 미만)
- [x] 가입 → 업로드 → 교정 피드백: MariaDB `feedbacks` 1행(user_id 연결) + `learning_samples` correction 1행,
      SQLite `jobs.feedback_saved=1`, SQLite 쪽 새 피드백 행 0 (확인 후 테스트 데이터 삭제)
- [x] pytest 전체 통과 (신규 8건)

### 4.2 부작용 / 리스크

- 학습 DB 가 fallback SQLite 인 동안 쌓인 기록은 MariaDB 로 옮겨지지 않고, 사이드카에서 다시 적재된다 (fallback 파일은 버려도 됨)
- 의사 라벨 5000건이 `pending` 으로 들어가 검수 목록이 커짐 → 콘솔에서 출처별 필터 필요

### 4.3 후속 작업

- `feature/feedback-review`: 운영 콘솔 학습 데이터 승인·삭제, RAG 는 승인된 교정만 사용

### 4.4 관련 문서

- `docs/plan/DATABASE.md`
