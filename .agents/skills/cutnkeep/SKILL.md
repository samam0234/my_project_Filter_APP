---
name: cutnkeep
description: "컷앤킵(CutNKeep) 프로젝트 규칙. 커밋 시 docs/branchs/commits 에 md 기록 필수(docs/commits 금지), 제목 요약 한국어(type/scope 영어), feature 브랜치, develop·main --no-ff, YOLO26s-seg·Ollama E4B. 트리거: commit, branchs, commits, console, backend, cutnkeep, ollama, yolo."
---

# 컷앤킵 프로젝트 스킬

## 프로젝트

- 이름: 컷앤킵 / Cut & Keep  
- 루트: `backend/`, `frontend/`, `console/`, `docs/`, `docker-compose.yml`  
- Phase 1: 단일 이미지 파이프라인, 계층형 백엔드, SQLite/MariaDB, 운영 콘솔  
- 비전: **YOLO26s-seg** (기본 s; n→s 안내 `docs/plan/YOLO26S_DEFAULT.md`)  
- LLM 기본: **Ollama gemma4:e4b** · 고도화: OpenAI/Gemini  
  → `docs/plan/AI_MODEL_STRATEGY.md`
- Python 의존성: **저장소 루트** `requirements.txt` / `requirements.docker.txt`

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
| **type / scope** | **영어** (`feat`, `fix`, `backend` …) |
| **제목 요약** | **한국어** (`feat(tts): 음성 인식 추가`) |
| **본문** | **한국어** |
| **바닥글** | **한국어** |

### 제목 규칙

```text
feat(tts): 음성 인식 추가          ✅
feat(llm): add to engine           ❌ 요약 영어 금지
```

형식: `type(scope): <한국어 한 줄 요약>`  
상세: `docs/guidance/commit-message.md`

## 커밋 기록 (필수 · 예외 없음)

**경로 (이것만 사용):** `docs/branchs/commits/`  
**금지:** `docs/commits/` 등 다른 경로에 남기기 · 기록 생략 · “나중에” · 푸시만 하고 끝내기

에이전트는 **커밋을 하거나 하기 전에 무조건** 아래 md 를 남긴다.

```text
docs/branchs/commits/YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

| 규칙 | 내용 |
|------|------|
| 시점 | **커밋 직전(초안)** 또는 **커밋 직후(SHA 확정)** — 둘 중 하나 이상, **무조건** |
| 템플릿 | `docs/branchs/TEMPLATE.md` 준수 (한 줄 요약만 금지) |
| 후속 | 기록 파일도 **같은 브랜치에 커밋** (`docs(branchs): …`) 후 push |
| 대상 | 기능·docs·merge·chore 커밋 모두. “작다”고 생략 금지 |
| 파일명 | `YYMMDD_HHMM` + short SHA + kebab name + 브랜치(`/`→`-`) |

체크리스트 (커밋/푸시 전):

- [ ] `docs/branchs/commits/*.md` 작성했는가  
- [ ] 파일명 규칙 맞는가  
- [ ] 템플릿 섹션 채웠는가  
- [ ] 기록 파일도 git 에 올렸는가  

## 브랜치 (필수)

- 작업·커밋: `feature/*` 등에서만  
- 통합: **`develop` / `main` 만**, 병합 시 **`git merge --no-ff` (FF 금지)**  
- 가이드: `docs/guidance/branch-merge.md`

## Docker

`docker compose -p cut_and_keep ...` · Redis 호스트 포트 `6380` 주의  
backend 빌드 context = **저장소 루트** (`dockerfile: backend/Dockerfile`)

## 안전

- `.env` 시크릿 커밋 금지  
- force-push 금지 (사용자 요청 시 제외)  
