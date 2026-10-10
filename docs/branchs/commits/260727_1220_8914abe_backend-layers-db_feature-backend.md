# Schema, router, repository + dual DB / `8914abe`

> 브랜치: `feature/backend`  
> 작성일: `2026-07-27`  
> 작성자: project

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(backend): add schema, router, repository layers and dual database` |
| **커밋 번호 (SHA)** | `8914abe4ffef5de5a59989a557ad303491ebdc10` |
| **짧은 SHA** | `8914abe` |
| **브랜치** | `feature/backend` (이후 develop merge) |
| **부모 커밋** | `1342117` |

## 2. 주 커밋 내용

- Pydantic DTO를 `schemas/`로 분리
- HTTP 계층을 `routers/`로 명시
- SQLAlchemy ORM `models/` + `repositories/` 추가
- SQLite(local) / MariaDB(prod) dual dialect
- Job/Feedback DB 저장, jobs 조회 API
- `docs/plan/DATABASE.md` 작성

## 3. 상세 내용

### 3.1 배경 / 목적
스키마·라우터·레포지토리 계층이 보이지 않던 구조를 정리하고, 처리 메타데이터를 DB에 남긴다.

### 3.2 변경 범위
- 추가: `backend/app/db`, `repositories`, `routers`, `schemas`, ORM tables
- 수정: config, main, services, workflows, compose, docs
- 삭제: 구 `api/endpoints` 구조

### 3.3 기술 포인트
- `DB_DIALECT` + `DATABASE_URL` 우선순위
- `init_db()` create_all (Phase 1)
- 피드백: DB + 파일 사이드카 병행

### 3.4 의도적으로 하지 않은 것
- Alembic
- 관리자 콘솔 UI
- 배치 실제 워커

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 코드 구조 반영
- [ ] (당시) Docker 전체 기동은 후속 커밋
- 결과: 계층·DB 설계 문서와 코드 동기화

### 4.2 부작용 / 리스크
- 전체 requirements에 torch/ultralytics 포함 시 Docker 빌드 장기화 → docker 커밋에서 slim 분리

### 4.3 후속 작업
- Docker 스택 안정화 (`8157388`)
- Console 앱

### 4.4 관련 문서
- `docs/plan/DATABASE.md`
- `docs/Architecture/layers.md` (후속 정리)
