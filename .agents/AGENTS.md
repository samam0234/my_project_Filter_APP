# 컷앤킵 — 에이전트 지시

**컷앤킵 (Cut & Keep / CutNKeep)** 작업 중: 프롬프트 기반 선택적 배경 제거  
(FastAPI + React 사용자 앱 + React 운영 콘솔 + SQLite/MariaDB).

## 항상 읽고 따를 것

1. `.agents/SKILL.md` — 전체 스킬 규칙  
2. `docs/guidance/commit-message.md` — 커밋 언어 규칙  
3. `docs/branchs/TEMPLATE.md` — 커밋 기록 템플릿  
4. 백엔드 작업 시 `docs/plan/LOGIC_STRUCTURE.md` / `DATABASE.md`  
5. 병합 시 `docs/guidance/branch-merge.md`  

## 커밋 메시지 (필수)

```
제목: 영어만 (Conventional Commits)
본문: 한국어
바닥글: 한국어
```

예시:

```
feat(backend): add job list endpoint

Job 조회 API를 추가하고 콘솔에서 사용 가능하게 함.

관련: docs/guidance/console-admin.md
```

## 커밋 후

`docs/branchs/commits/YYMMDD_HHMM_[sha]_[이름]_[브랜치].md` 작성 (템플릿 준수).  
예: `260727_1446_..._feature-docs.md` (날짜+시분). 브랜치 `/` → `-`.

## 브랜치

| 작업 | 브랜치 |
|------|--------|
| API, DB, 계층 | `feature/backend` |
| 사용자 UI | `feature/frontend` |
| 운영 콘솔 / 문서 허브 | `feature/docs` |
| OpenCV | `feature/opencv` |
| YOLO | `feature/yolo` |

- **커밋은 작업 브랜치(`feature/*` 등)에서만**  
- **일자 통합 병합 대상: `develop` 또는 `main` 만**  
- feature → feature 장기 통합 금지  
- 가이드: `docs/guidance/branch-merge.md`  
- 사용자 승인 없이 `main`/`develop` force-push 금지  

## 스택

- `backend/` — FastAPI, routers, schemas, repositories, models, db  
- `frontend/` — 사용자 앱 :5173  
- `console/` — 운영 콘솔 :5174  
- Docker 프로젝트명: `cut_and_keep`  
