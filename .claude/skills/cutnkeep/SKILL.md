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

## 병합 시점 (절대 규칙)

- **브랜치 하나(작업 하나)를 끝낼 때마다 `develop` / `main` 에 병합하지 않는다.**
  브랜치에서는 **커밋 + 커밋 기록(md)** 까지만 한다.
- 사용자가 준 **파트 작업을 각 브랜치에 모두 커밋한 뒤, 전부 끝났을 때 한 번에 총 병합**한다.
  (브랜치별 `git merge --no-ff`, 앞 브랜치 위에 쌓인 순서대로)
- "일단 병합해 두기", 파트 사이 중간 병합은 **금지**. 사용자가 시키지 않은 병합도 금지.
- 병합 기록 md 는 총 병합 때 한 번에 남긴다.
- 상세: `docs/guidance/branch-merge.md`
