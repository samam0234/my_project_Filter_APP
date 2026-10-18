# 문서 허브 · 에이전트 · 데이터 폴더 README 보강 / `fb09fd3d55d77995496aff40b3907b3406bf8d4b`

> 브랜치: `feature/readme-refresh`  
> 작성일: `2026-10-18 23:13`  
> 작성자: `agent`  
> 파일명: `261018_2313_fb09fd3_readme-docs-agents_feature-readme-refresh.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(readme): 문서 허브 · 에이전트 · 데이터 폴더 README 보강` |
| **커밋 번호 (SHA)** | `fb09fd3d55d77995496aff40b3907b3406bf8d4b` |
| **짧은 SHA** | `fb09fd3` |
| **브랜치** | `feature/readme-refresh` |
| **부모 커밋** | `9949f555fe41f007f19a4d81462e08464b634c50` |

## 2. 주 커밋 내용

- `docs/README.md` 를 처음 읽는 순서 · 상황별 문서 · 폴더 지도 · `plan/` 목록 · 문서 작성 규칙으로 다시 씀
- `docs/guidance` · `Architecture` · `repeater` · `find_debug` · `trainings` · `web_management` README 에 목적 · 읽는 순서 · 템플릿 추가
- `docs/vaildates/README.md` 위에 영역별 핵심 결과 표와 수치 읽는 법 추가 (기존 목록은 그대로)
- 에이전트 설정 README 8개(`.agents` · `.claude` · `.Codex` · `.antigravity` · `.cursor` · `.gemini` · `.git_Copilot` · `.grok`)를 같은 틀로 정리
- Chroma 폴더 README 3개 · `training/yolo/README.md` 보강, `training/README.md` 의 예전 경로 5곳 수정

## 3. 상세 내용

### 3.1 배경 / 목적

README 고도화 요청의 2차분이다. 1차(`5a94dd7`)에서 제품 · 배포 README 를 다시 썼고, 이번에는 문서 허브와 나머지 폴더 README 를 채웠다.

### 3.2 변경 범위

- 수정된 경로 (21개): `.agents/README.md`, `.claude/README.md`, `.Codex/README.md`, `.antigravity/README.md`, `.cursor/README.md`, `.gemini/README.md`, `.git_Copilot/README.md`, `.grok/README.md`, `data/chroma/README.md`, `backend/data/chroma/README.md`, `Portfolio/ai/data/chroma/README.md`, `docs/README.md`, `docs/Architecture/README.md`, `docs/find_debug/README.md`, `docs/guidance/README.md`, `docs/repeater/README.md`, `docs/trainings/README.md`, `docs/vaildates/README.md`, `docs/web_management/README.md`, `training/README.md`, `training/yolo/README.md`

### 3.3 기술 포인트

- 하위 문서를 제목만 보고 요약하지 않고 본문을 읽어 맞췄다 (`find_debug/2026-07-27.md` 는 Redis 포트 충돌 · import 오류, `backend-import-engine.md` 는 없는 이름 import)
- `vaildates` 요약 표의 숫자는 각 근거 문서의 기존 설명에서 그대로 옮겼다
- 에이전트 README 는 규칙을 복제하지 않고 정본(`AGENTS.md` · `.agents/skills/cutnkeep/SKILL.md`)을 가리키며, 요약이 다르면 정본이 맞다고 적었다
- 확인 중 찾은 설정 불일치는 README 에 사실만 적고 설정 파일은 고치지 않았다
  - `.gemini/GEMINI.md` 가 폐기된 경로 `.agents/SKILL.md` 를 가리킴
  - `.github/copilot-instructions.md` 와 `.git_Copilot/copilot-instructions.md` 내용이 다름
  - `.claude/skills/cutnkeep/SKILL.md` description 이 예전 표현("커밋 제목 영어")
- `training/yolo/apply_best.py` 의 실제 기본 대상(`backend/models/yolo26s-seg.pt`)을 적고, 서빙 기본 m 을 바꿀 때 `--dest` 를 쓰라고 안내

### 3.4 의도적으로 하지 않은 것

- `training/README.md` · `training/lora/README.md` · `docs/branchs/README.md` · `docker/mariadb/README.md` · `Scribble/README.md` 는 이미 길고 자세해 다시 쓰지 않음 (`training/README.md` 는 예전 경로만 수정)
- 에이전트 설정 파일 · `.env.example` 수정

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `pytest tests/structure` — 13개 중 12개 통과. 남은 1개는 `.env.example` 의 `PROMPT_CHROMA_*` 누락 (develop 에서도 같은 기존 실패)
- [x] 바꾼 md 21개의 상대 링크 검사 — 깨진 링크 0
- 결과 서술: 문서만 바꿨다

### 4.2 부작용 / 리스크

- `vaildates` 요약 표는 개별 문서와 이중으로 수치를 가진다. 실험을 다시 하면 둘 다 고쳐야 한다

### 4.3 후속 작업

- 사용자 확인 후: `.env.example` 의 `PROMPT_CHROMA_*` 추가, `.gemini/GEMINI.md` 경로 · Copilot 지시 · `.claude` 스킬 description 정리
- 병합은 전체 작업이 끝난 뒤 사용자 지시로

### 4.4 관련 문서

- `docs/branchs/commits/261018_2306_5a94dd7_readme-product-docs_feature-readme-refresh.md`
