---
name: cutnkeep
description: >
  컷앤킵 저장소 Grok 규칙: 커밋 제목 영어·본문/바닥글 한국어,
  branchs 로그 YYMMDD_HHMM_*, 백엔드 계층, console vs frontend.
  이 저장소 작업 전반에 사용. /cutnkeep
---

# Grok 스킬 — 컷앤킵

정본 스킬을 따른다:

**읽고 준수:** `.agents/SKILL.md`, `.agents/AGENTS.md`

### 커밋 (요약)

- 제목: **영어만** (`feat(scope): ...`)  
- 본문: **한국어**  
- 바닥글: **한국어**  

가이드: `docs/guidance/commit-message.md`

### 커밋 기록 파일

`docs/branchs/commits/YYMMDD_HHMM_[sha]_[이름]_[브랜치].md`  
예: `260727_1446_5420cfb_console-and-docs-hub_feature-docs.md`

### 브랜치

- 작업은 `feature/*` 에서만  
- 일자 통합 병합은 **`develop` 또는 `main` 에만**  
- 가이드: `docs/guidance/branch-merge.md`  
