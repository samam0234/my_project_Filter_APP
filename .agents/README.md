# .agents — 공통 에이전트 스킬 허브

Grok 등이 스킬을 찾는 경로: **`.agents/skills/<name>/SKILL.md`**

| 경로 | 용도 |
|------|------|
| [`skills/cutnkeep/SKILL.md`](./skills/cutnkeep/SKILL.md) | **정본 스킬** (자동 발견) |
| [`AGENTS.md`](./AGENTS.md) | 짧은 진입 지시 |
| 루트 [`../AGENTS.md`](../AGENTS.md) | Grok 프로젝트 규칙 자동 로드 |

## 잘못된 예전 경로 (사용 금지)

- ~~`.agents/SKILL.md`~~ → `skills/cutnkeep/SKILL.md` 로 이동됨  
  (스킬 루트에 바로 두면 도구가 못 찾거나 경고가 날 수 있음)

## 도구별 어댑터

`.grok/skills/`, `.claude/skills/`, `.cursor/skills/`, `.gemini/skills/` 등  
각 폴더에도 `cutnkeep/SKILL.md` 가 있고 정본을 가리킨다.
