---
name: cutnkeep
description: "컷앤킵 Grok 스킬. 커밋 제목 영어/본문·바닥글 한국어, YYMMDD_HHMM branchs 로그, feature 브랜치, --no-ff 병합, YOLO·Ollama. 저장소 작업 전반. /cutnkeep"
---

# Grok 스킬 — 컷앤킵

**정본과 동일 규칙:** `.agents/skills/cutnkeep/SKILL.md`  
**프로젝트 규칙:** 루트 `AGENTS.md`, `.agents/AGENTS.md`

### 커밋

- 제목: 영어 · 본문/바닥글: 한국어  
- `docs/guidance/commit-message.md`

### 기록 파일

`docs/branchs/commits/YYMMDD_HHMM_[sha]_[이름]_[브랜치].md`

### 브랜치

- 작업: `feature/*`  
- develop/main 병합: **`git merge --no-ff` 필수**  
- `docs/guidance/branch-merge.md`
