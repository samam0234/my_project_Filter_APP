# GitHub Copilot — 컷앤킵

이 파일은 본 저장소의 Copilot Chat / 코딩 에이전트용이다.

## 프로젝트

컷앤킵: 프롬프트 기반 배경 제거.  
`backend` FastAPI, `frontend` 사용자 UI (:5173), `console` 운영 UI (:5174).

## 커밋 메시지 (필수)

커밋 제안·생성 시:

```
type(scope): English summary

한국어로 본문 작성

한국어로 바닥글 작성 (선택)
```

- 제목에 **한글 금지**  
- 본문·바닥글은 **한국어**  
- 상세: `docs/guidance/commit-message.md`

## 아키텍처

Routers → services/workflows → repositories → models.  
schemas 는 Pydantic DTO 전용.

## 브랜치

- 작업 커밋: `feature/*`  
- 일자 병합: `develop` / `main` 만  
- `docs/guidance/branch-merge.md`

## 커밋 후 문서

`docs/branchs/commits/YYMMDD_HHMM_[id]_[이름]_[브랜치].md`  
예: `260727_1446_...` · 템플릿: `docs/branchs/TEMPLATE.md`

## 전체 스킬

`.agents/skills/cutnkeep/SKILL.md` · 루트 `AGENTS.md`
