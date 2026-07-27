---
name: cutnkeep
description: "컷앤킵(CutNKeep) 프로젝트 규칙. 커밋 제목 영어/본문·바닥글 한국어, feature 브랜치, develop·main 은 --no-ff 병합, YOLO26n-seg·Ollama E4B, backend 계층. 코딩·커밋·문서·Docker 작업 시 사용. 트리거: commit, branchs, console, backend, cutnkeep, ollama, yolo."
---

# 컷앤킵 프로젝트 스킬

## 프로젝트

- 이름: 컷앤킵 / Cut & Keep  
- 루트: `backend/`, `frontend/`, `console/`, `docs/`, `docker-compose.yml`  
- Phase 1: 단일 이미지 파이프라인, 계층형 백엔드, SQLite/MariaDB, 운영 콘솔  
- 비전: **YOLO26n-seg** · LLM 기본: **Ollama gemma4:e4b** · 고도화: OpenAI/Gemini  
  → `docs/plan/AI_MODEL_STRATEGY.md`

## 백엔드 아키텍처

```
routers → services/workflows → repositories → models
routers → schemas
```

- 라우터에 SQL 금지. 레포지토리에 OpenCV 금지.  
- DB: `DB_DIALECT=sqlite|mariadb` → `docs/plan/DATABASE.md`  
- OpenCV 위치: `backend/app/services/image_processor.py`, `effects.py`, `utils/image_utils.py`

## 앱

| 경로 | 역할 | 포트 |
|------|------|------|
| `frontend/` | 사용자 필터 UI | 5173 |
| `console/` | 운영 관리자 | 5174 |
| `backend/` | API | 8000 |

## Git 커밋 (필수)

| 구간 | 언어 |
|------|------|
| **제목** | **영어만** `type(scope): summary` |
| **본문** | **한국어** |
| **바닥글** | **한국어** |

상세: `docs/guidance/commit-message.md`

## 커밋 후 기록

`docs/branchs/commits/YYMMDD_HHMM_[id]_[name]_[branch].md`  
템플릿: `docs/branchs/TEMPLATE.md`

## 브랜치 (필수)

- 작업·커밋: `feature/*` 등에서만  
- 통합: **`develop` / `main` 만**, 병합 시 **`git merge --no-ff` (FF 금지)**  
- 가이드: `docs/guidance/branch-merge.md`

## Docker

`docker compose -p cut_and_keep ...` · Redis 호스트 포트 `6380` 주의

## 안전

- `.env` 시크릿 커밋 금지  
- force-push 금지 (사용자 요청 시 제외)  
