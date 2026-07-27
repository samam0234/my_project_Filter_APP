# 컷앤킵 — 프로젝트 규칙 (AGENTS.md)

Grok / Codex / 호환 에이전트가 저장소 루트에서 자동 로드하는 **프로젝트 규칙**이다.

상세 스킬: [`.agents/skills/cutnkeep/SKILL.md`](.agents/skills/cutnkeep/SKILL.md)  
요약 복제: [`.agents/AGENTS.md`](.agents/AGENTS.md)

## 한눈에

| 항목 | 규칙 |
|------|------|
| 커밋 제목 | **영어** (Conventional Commits) |
| 커밋 본문·바닥글 | **한국어** |
| 작업 브랜치 | `feature/*` 등 |
| 통합 브랜치 | `develop` / `main` 만 |
| 병합 | **`git merge --no-ff`** (FF 금지) |
| 커밋 기록 파일 | `docs/branchs/commits/YYMMDD_HHMM_[id]_[name]_[branch].md` |
| 비전 | YOLO26n-seg |
| LLM 기본 | Ollama `gemma4:e4b` |
| OpenCV 위치 | `backend/app/services/image_processor.py`, `effects.py` |

## 실행

- 가이드: [`RUN.md`](./RUN.md)  
- console: `cd console && npm install && npm run dev` (5174)  
- backend: Python **3.11** venv + `requirements.txt` (3.14 비권장)

## 문서 허브

[`docs/README.md`](./docs/README.md)
