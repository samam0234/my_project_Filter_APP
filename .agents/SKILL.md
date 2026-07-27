---
name: cutnkeep-project
description: >
  컷앤킵(CutNKeep) 프로젝트 규칙: 백엔드 계층, SQLite/MariaDB, 커밋 제목 영어·본문/바닥글 한국어,
  branchs 로그 파일명 YYMMDD_HHMM_*, feature 브랜치 선택, console vs frontend.
  이 저장소에서 코딩·커밋·문서·Docker 작업 시 사용. 트리거: commit, branchs, console, backend, cut_and_keep.
---

# 컷앤킵 프로젝트 스킬

## 프로젝트

- 이름: 컷앤킵 / Cut & Keep  
- 루트: `backend/`, `frontend/`, `console/`, `docs/`, `docker-compose.yml`  
- Phase 1: 단일 이미지 파이프라인, 계층형 백엔드, 로컬 SQLite / Docker MariaDB, 운영 콘솔  

## 백엔드 아키텍처

허용 의존 방향:

```
routers → services/workflows → repositories → models
routers → schemas
```

- 라우터에 SQL 넣지 말 것. 레포지토리에 OpenCV 넣지 말 것.  
- DB: `DB_DIALECT=sqlite|mariadb` → `docs/plan/DATABASE.md`  

## 앱

| 경로 | 역할 | 포트 |
|------|------|------|
| `frontend/` | 사용자 필터 UI | 5173 |
| `console/` | 운영 관리자 (Job/헬스) | 5174 |
| `backend/` | API | 8000 |

## Git 커밋 (언어 필수)

| 구간 | 언어 |
|------|------|
| **제목 (subject)** | **영어만** — `type(scope): summary` |
| **본문** | **한국어** |
| **바닥글** | **한국어** |

### 제목 규칙

- Conventional Commits: `feat|fix|docs|chore|refactor|test|perf|ci|build`
- scope 예: `backend`, `frontend`, `console`, `docker`, `docs`, `branchs`
- 끝에 마침표 금지, 명령형 (`add`, `added` 아님)

### 본문 · 바닥글

- 무엇을·왜 바꿨는지 한국어로  
- 바닥글 예: `관련:`, `후속:`, `Breaking-Change:` (설명은 한국어)

### 전체 예시

```
feat(docker): add cut_and_keep compose stack with slim backend image

Docker Compose 프로젝트명 cut_and_keep으로 스택을 구성함.
백엔드는 경량 requirements.docker.txt를 사용함.

관련: docs/Architecture/docker-topology.md
후속: console 서비스 compose 등록 검토
```

상세: `docs/guidance/commit-message.md`

## 커밋 후 — branchs 기록 파일

1. `docs/branchs/TEMPLATE.md` 구조 복사  
2. 파일명 **필수**:

```text
YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

예: `260727_1446_5420cfb_console-and-docs-hub_feature-docs.md`  
- `YYMMDD` = 날짜 (예: 260727)  
- `HHMM` = 시분 (예: 1446 = 14:46, 커밋 시각)  
- 브랜치 `/` → `-`  

3. `docs/branchs/README.md` 표 갱신  

## 브랜치 선택

- **일상 작업·커밋:** 해당 `feature/*` (또는 bugfix/experimental) **에서만**  
- **일자 통합 라인:** **`develop` 또는 `main` 에만** merge  
- feature끼리 장기간 merge 하며 통합하지 말 것  
- 작업 끝나면 → **`develop`에 merge**  
- 배포: `release/*` → **`main`**  
- 가이드: `docs/guidance/branch-merge.md`, `docs/branchs/BRANCH_MAP.md`  

## Docker

- 프로젝트: `docker compose -p cut_and_keep ...`  
- Redis 호스트 포트 보통 `6380` (6379 충돌 회피)  
- Docker Desktop Images 목록이 전역인 것은 정상 (다른 프로젝트와 섞여 보임)  

## 문서 허브

운영 지식은 맞는 폴더에:

- `docs/Architecture/` · `docs/branchs/` · `docs/find_debug/`  
- `docs/guidance/` · `docs/trainings/` · `docs/repeater/`  
- `docs/vaildates/` · `docs/web_management/` · `docs/plan/`  

## 안전

- `.env` 시크릿 커밋 금지  
- 사용자 요청 없이 `main`/`develop` force-push 금지  
- 작고 리뷰 가능한 커밋 선호  

## 코드 작업 완료 기준

- 계층 규칙 준수  
- 커밋 메시지 언어 규칙 준수  
- 기록 요청 시 branchs 로그 파일 작성  
