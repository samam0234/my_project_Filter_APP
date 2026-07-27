# Claude — 컷앤킵

이 저장소는 공유 에이전트 규칙을 사용한다.

**주 지시:** `.agents/AGENTS.md`, `.agents/SKILL.md`

## 커밋 메시지

- **제목:** 영어만 (Conventional Commits)  
- **본문:** 한국어  
- **바닥글:** 한국어  

→ `docs/guidance/commit-message.md`

## 커밋 후

`docs/branchs/commits/YY_MM_DD_[id]_[이름]_[브랜치].md` 작성  
(`docs/branchs/TEMPLATE.md` 준수)

## 브랜치

- 작업 커밋: `feature/*`  
- 일자 병합: `develop` / `main` 만  
→ `docs/guidance/branch-merge.md`

## 스택

- `backend/` FastAPI · `frontend/` :5173 · `console/` :5174  
- Docker: `-p cut_and_keep`
