# 컷앤킵 에이전트 지침

**원본 스킬 경로:** `.agents/skills/cutnkeep/SKILL.md`  
**루트 규칙:** `AGENTS.md` (Grok 프로젝트 규칙 자동 로드)

## 자주 여는 문서

1. `.agents/skills/cutnkeep/SKILL.md`  
2. `docs/guidance/commit-message.md`  
3. `docs/guidance/branch-merge.md`  
4. `docs/branchs/TEMPLATE.md`  
5. 백엔드 작업 시 `docs/plan/LOGIC_STRUCTURE.md`, `DATABASE.md`, `AI_MODEL_STRATEGY.md`

## 커밋

```text
type(scope): 한국어 요약

한국어 본문

한국어 바닥글
```

- type/scope 만 영어  
- 제목 요약은 **한글** (`feat(tts): 음성 인식 추가`)  
- 영어 요약 금지 (`feat(llm): add to engine` ❌)

## 브랜치

- 작업: `feature/*`  
- develop/main 병합: **`git merge --no-ff` 필수**  
- FF 만 쓰면 Git Graph 가 일자로 보임  

## 스택

- backend FastAPI · frontend :5173 · console :5174  
- Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
- Docker: `-p cut_and_keep`, backend build context = 저장소 루트  
