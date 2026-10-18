# .git_Copilot — GitHub Copilot 프로젝트 지시

> GitHub Copilot가 이 저장소에서 읽는 프로젝트 지시. **규칙의 정본은 여기가 아니라** 루트 [`AGENTS.md`](../AGENTS.md)와 [`.agents/skills/cutnkeep/SKILL.md`](../.agents/skills/cutnkeep/SKILL.md)다.

Copilot 지시를 모아 두는 폴더다. Copilot은 버전에 따라 `.github/copilot-instructions.md`만 읽으므로, 그 경로에도 같은 내용을 둔다.

## 이 폴더의 파일

| 파일 | 역할 |
|------|------|
| `copilot-instructions.md` | 메인 Copilot 지시 |
| `instructions.md` | 별칭 포인터 — 메인 지시를 가리킨다 |

`.github/copilot-instructions.md`(실제로 읽히는 경로)와 이 폴더의 `copilot-instructions.md`는 **같은 내용**이어야 한다. 하나를 고치면 다른 하나도 고친다. **2026-10-18 확인 시 두 파일의 내용이 다르다** — 맞추는 일이 남아 있다.

## 이 저장소의 핵심 규칙 (요약)

규칙 본문은 정본에만 있다. 아래는 찾아보기용 요약이고, 다르면 **정본이 맞다.**

| 항목 | 규칙 |
|------|------|
| 대화 언어 | 사용자가 한국어로 말하면 중간 안내 · 질문 · 보고까지 **모두 한국어** |
| 커밋 메시지 | type / scope 영어, **제목 요약 · 본문 · 바닥글 한국어** (`feat(tts): 음성 인식 추가`) |
| 커밋 기록 | 커밋마다 `docs/branchs/commits/`에 기록 md (템플릿 `docs/branchs/TEMPLATE.md`) — `docs/commits/` 금지 |
| 브랜치 · 병합 | 작업은 `feature/*`, 통합은 `develop` / `main`만 `--no-ff`. **파트가 모두 끝난 뒤 사용자가 시킬 때만 한 번에** 병합 |
| 비밀 값 | 앱 비밀번호 · SSH 키 · `EDGE_SECRET` · `.env`를 요청 · 출력 · 기록하지 않는다 |
| 운영 | 사용자 PC의 실행 중 서버를 죽이지 않는다. 확인하지 않은 것을 "된다"고 말하지 않는다 |
| 현재 상태 | [`docs/HANDOVER.md`](../docs/HANDOVER.md)를 먼저 읽는다 |

## 규칙을 바꿀 때

1. **정본을 먼저 고친다** — 루트 [`AGENTS.md`](../AGENTS.md)와 [`.agents/skills/cutnkeep/SKILL.md`](../.agents/skills/cutnkeep/SKILL.md)
2. 이 폴더의 파일은 정본을 가리키거나 요약만 하므로, 요약이 달라졌으면 같은 커밋에서 맞춘다
3. 도구별 폴더(`.claude` · `.cursor` · `.gemini` · `.grok` · `.Codex` · `.antigravity` · `.git_Copilot`)가 서로 다른 말을 하지 않게 한다

관련: 에이전트 허브 [`.agents/README.md`](../.agents/README.md) · 사람용 규칙 [`docs/guidance/commit-message.md`](../docs/guidance/commit-message.md) · [`docs/guidance/branch-merge.md`](../docs/guidance/branch-merge.md)
