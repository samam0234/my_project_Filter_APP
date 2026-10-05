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
- **커밋 기록 필수:** `docs/branchs/commits/YYMMDD_HHMM_….md`  
  - 커밋 전·후 **무조건** 작성 · `docs/commits/` 금지  
  - 템플릿: `docs/branchs/TEMPLATE.md`

## 브랜치

- 작업: `feature/*`  
- develop/main 병합: **`git merge --no-ff` 필수**  
- FF 만 쓰면 Git Graph 가 일자로 보임  

## 스택

- backend FastAPI · frontend :5173 · console :5174  
- Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
- Docker: `-p cut_and_keep`, backend build context = 저장소 루트  

## 병합 시점 (절대 규칙)

- **브랜치 하나(작업 하나)를 끝낼 때마다 `develop` / `main` 에 병합하지 않는다.**
  브랜치에서는 **커밋 + 커밋 기록(md)** 까지만 한다.
- 사용자가 준 **파트 작업을 각 브랜치에 모두 커밋한 뒤, 전부 끝났을 때 한 번에 총 병합**한다.
  (브랜치별 `git merge --no-ff`, 앞 브랜치 위에 쌓인 순서대로)
- "일단 병합해 두기", 파트 사이 중간 병합은 **금지**. 사용자가 시키지 않은 병합도 금지.
- 병합 기록 md 는 총 병합 때 한 번에 남긴다.
- 상세: `docs/guidance/branch-merge.md`
