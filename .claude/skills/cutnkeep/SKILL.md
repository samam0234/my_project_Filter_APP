---
name: cutnkeep
description: "컷앤킵 Claude 스킬. 커밋 제목 영어, 본문·바닥글 한국어. feature 브랜치, --no-ff 병합, branchs 파일명 규칙."
---

# Claude 스킬 — cutnkeep

정본: `.agents/skills/cutnkeep/SKILL.md`  
프로젝트 지시: `.claude/CLAUDE.md`, 루트 `AGENTS.md`

커밋 예:

```
feat(scope): english title

한국어 본문

한국어 바닥글
```

기록: `docs/branchs/commits/YYMMDD_HHMM_[sha]_[이름]_[브랜치].md`  
병합: `git merge --no-ff feature/xxx`
