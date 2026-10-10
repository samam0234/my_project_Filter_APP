# 병합 시점 절대 규칙 — 브랜치마다 병합 금지, 전체 파트 후 총 병합 / `ac6216d4b208a2954c4434a9820af94a4f69b558`

> 브랜치: `feature/agent-rules`  
> 작성일: `2026-10-06 05:32`  
> 작성자: `agent`  
> 파일명: `261006_0532_ac6216d_merge-timing-rule_feature-agent-rules.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(rules): 병합 시점 절대 규칙 — 브랜치마다 병합 금지, 전체 파트 후 총 병합` |
| **커밋 번호 (SHA)** | `ac6216d4b208a2954c4434a9820af94a4f69b558` |
| **짧은 SHA** | `ac6216d` |
| **브랜치** | `feature/agent-rules` |
| **부모 커밋** | `8f8bbd4` (develop) |

## 2. 주 커밋 내용

- 모든 에이전트 규칙 파일과 스킬, `docs/guidance/branch-merge.md` 에 같은 규칙을 추가
  - 브랜치 하나 끝날 때마다 develop/main 에 병합하지 않는다 (브랜치에서는 커밋 + 커밋 기록까지만)
  - 사용자가 준 파트를 각 브랜치에 모두 커밋한 뒤 전부 끝났을 때 한 번에 총 병합 (`--no-ff`, 쌓인 순서대로)
  - 중간 병합·지시 없는 병합 금지, 병합 기록 md 도 총 병합 때 한 번에

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 지적: 파트 작업마다 develop 에 병합했다 ("병합 자주 하지 말라고 했잖아").
같은 실수를 에이전트가 반복하지 않도록 모든 에이전트 지시 파일과 문서에 못 박는다.

### 3.2 변경 범위 (20개 파일)

- 루트·에이전트: `AGENTS.md`, `.agents/AGENTS.md`, `.claude/CLAUDE.md`, `.Codex/AGENTS.md`, `.antigravity/AGENTS.md`,
  `.gemini/GEMINI.md`, `.github/copilot-instructions.md`, `.git_Copilot/copilot-instructions.md`,
  `.cursor/rules/cutnkeep.mdc`, `.grok/rules/cutnkeep.md`
- 스킬 7개: `.{agents,Codex,antigravity,claude,cursor,gemini,grok}/skills/cutnkeep/SKILL.md`
- 문서: `docs/guidance/branch-merge.md` (0장 신설·흐름·체크리스트), `docs/guidance/README.md`, `docs/branchs/README.md`

### 3.3 기술 포인트

- 파일마다 형식이 달라 같은 문구 블록(`## 병합 시점 (절대 규칙)`)을 끝에 붙이고, 자주 읽히는 `CLAUDE.md`·`AGENTS.md` 는 본문 위쪽에도 한 줄 추가
- Claude 개인 기억(`feedback-merge-only-at-end`)에도 저장

### 3.4 의도적으로 하지 않은 것

- 과거 병합 기록 수정 (이전에 정상적으로 병합된 브랜치는 그대로)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 20개 파일에 규칙 문구 존재 확인 (grep)
- [x] 이 규칙에 따라 이번 총 병합을 한 번에 수행

### 4.2 부작용 / 리스크

- 없음 (문서 변경)

### 4.3 후속 작업

- 앞으로 모든 작업: 브랜치마다 커밋·기록만, 병합은 전체 파트 완료 후 한 번에

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
