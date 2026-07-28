# Claude — 컷앤킵

이 저장소는 공유 에이전트 규칙을 사용한다.

**주 지시:** 루트 `AGENTS.md`, `.agents/skills/cutnkeep/SKILL.md`

## 커밋 메시지

- **type / scope:** 영어 (`feat`, `fix`, `backend` …)  
- **제목 요약:** **한국어** (`feat(tts): 음성 인식 추가`)  
- **본문·바닥글:** 한국어  
- 영어 요약 금지: `feat(llm): add to engine` ❌  

→ `docs/guidance/commit-message.md`

## 커밋 후

`docs/branchs/commits/YYMMDD_HHMM_[id]_[이름]_[브랜치].md` 작성  
(`docs/branchs/TEMPLATE.md` 준수, 예: `260727_1446_...`)

## 브랜치

- 작업 커밋: `feature/*`  
- 일자 병합: `develop` / `main` 만  
→ `docs/guidance/branch-merge.md`

## 스택

- `backend/` FastAPI · `frontend/` :5173 · `console/` :5174  
- Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
- Docker: `-p cut_and_keep`  
