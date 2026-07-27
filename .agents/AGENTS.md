# 컷앤킵 — 에이전트 지시

**정본 스킬 경로:** `.agents/skills/cutnkeep/SKILL.md`  
**루트 규칙:** `AGENTS.md` (Grok 프로젝트 규칙 자동 로드)

## 항상 따를 것

1. `.agents/skills/cutnkeep/SKILL.md`  
2. `docs/guidance/commit-message.md`  
3. `docs/guidance/branch-merge.md`  
4. `docs/branchs/TEMPLATE.md`  
5. 백엔드 작업 시 `docs/plan/LOGIC_STRUCTURE.md`, `DATABASE.md`, `AI_MODEL_STRATEGY.md`

## 커밋

```
type(scope): english title

한국어 본문

한국어 바닥글
```

## 브랜치

- 작업: `feature/*`  
- develop/main 병합: **`git merge --no-ff` 필수**  
- FF 로 합치면 Git Graph 가 다시 일자로 보임  

## 스택

- `backend/` FastAPI · `frontend/` :5173 · `console/` :5174  
- OpenCV: `backend/app/services/`  
- Docker: `-p cut_and_keep`
