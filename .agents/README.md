# .agents — 에이전트 공통 규칙 · 스킬 허브

> 이 저장소에서 일하는 모든 AI 코딩 에이전트(Claude · Codex · Cursor · Gemini · Copilot · Grok · Antigravity)가 따르는 **규칙의 정본**이 있는 곳.

에이전트마다 읽는 파일 위치가 달라서 도구별 폴더가 따로 있지만, 규칙 본문은 **두 곳에만** 있다.

| 정본 | 역할 |
|------|------|
| 루트 [`../AGENTS.md`](../AGENTS.md) | 프로젝트 규칙 — 저장소 루트에서 자동으로 읽히는 한눈 표 (언어 · 커밋 · 브랜치 · 스택 · 계정 · 배포 · 설명 사이트) |
| [`skills/cutnkeep/SKILL.md`](./skills/cutnkeep/SKILL.md) | **정본 스킬** — 상세 규칙 (자동 발견 경로 `.agents/skills/<name>/SKILL.md`) |
| [`AGENTS.md`](./AGENTS.md) | 짧은 진입 지시 (요약 복제) |

현재 운영 상태 · 접근 방법 · 함정은 규칙이 아니라 [`docs/HANDOVER.md`](../docs/HANDOVER.md)에 있다. 작업 전에 먼저 읽는다.

## 도구별 어댑터

| 도구 | 폴더 | 읽는 파일 |
|------|------|-----------|
| Claude Code | [`.claude/`](../.claude/README.md) | `CLAUDE.md` · `skills/cutnkeep/SKILL.md` |
| OpenAI Codex | [`.Codex/`](../.Codex/README.md) | 루트 `AGENTS.md` · `.Codex/AGENTS.md` · 스킬 |
| Cursor | [`.cursor/`](../.cursor/README.md) | `rules/cutnkeep.mdc`(항상 적용) · 스킬 |
| Gemini | [`.gemini/`](../.gemini/README.md) | `GEMINI.md` · 스킬 |
| GitHub Copilot | [`.git_Copilot/`](../.git_Copilot/README.md) · `.github/copilot-instructions.md` | `copilot-instructions.md` |
| Grok | [`.grok/`](../.grok/README.md) | 루트 `AGENTS.md` · `rules/cutnkeep.md` · 스킬 |
| Antigravity | [`.antigravity/`](../.antigravity/README.md) | `AGENTS.md` · 스킬 |

각 폴더의 `skills/cutnkeep/SKILL.md`는 정본을 가리키는 사본이다.

## 핵심 규칙 (찾아보기용 요약 — 다르면 정본이 맞다)

| 항목 | 규칙 |
|------|------|
| 대화 언어 | 사용자가 한국어로 말하면 중간 안내 · 질문 · 보고까지 **모두 한국어**. 코드 · 명령 · 경로 · 로그 원문은 그대로 |
| 커밋 메시지 | type / scope 영어, **제목 요약 · 본문 · 바닥글 한국어** — 영어 요약 금지 |
| 커밋 기록 | 커밋마다 `docs/branchs/commits/YYMMDD_HHMM_[id]_[이름]_[브랜치].md` — 생략 · 나중에 하기 금지, `docs/commits/` 금지 |
| 브랜치 | 작업은 `feature/*`, 통합은 `develop` / `main`만 `git merge --no-ff` |
| 병합 시점 | 브랜치 하나 끝날 때마다 병합 **금지**. 파트를 모두 커밋한 뒤 사용자가 시킬 때 한 번에 |
| 비밀 값 | 요청 · 출력 · 기록하지 않는다. 사용자가 직접 넣을 값은 스크립트로 안내하고 멈춘다 |
| 지시 | 사용자가 방법을 지정하면 그대로. 실행 중인 서버를 죽이지 않고, 만든 임시 계정 · 파일 · 컨테이너는 정리한다 |
| 보고 | 확인하지 않은 것을 "된다"고 말하지 않는다 |

## 잘못된 예전 경로 (사용 금지)

- ~~`.agents/SKILL.md`~~ → `skills/cutnkeep/SKILL.md`로 이동됨. 스킬 루트에 바로 두면 도구가 못 찾거나 경고가 난다.
  2026-10-18 확인 시 `.gemini/GEMINI.md`가 아직 이 예전 경로를 가리킨다.

## 규칙을 바꿀 때

1. 루트 `AGENTS.md`와 `skills/cutnkeep/SKILL.md`를 먼저 고친다.
2. 요약을 담은 어댑터(`.claude/CLAUDE.md` · `.cursor/rules/` · `.grok/rules/` · `.gemini/GEMINI.md` · Copilot 지시)가 달라지지 않게 같은 커밋에서 맞춘다.
3. 사람이 읽는 규칙 문서([`docs/guidance/commit-message.md`](../docs/guidance/commit-message.md) · [`docs/guidance/branch-merge.md`](../docs/guidance/branch-merge.md))도 함께 본다.
