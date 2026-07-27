# Multi-tool agent skills + commit guide / `4ccdc4d`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-27`  
> 작성자: project  
> 파일명: `260727_1456_4ccdc4d_agents-commit-guide_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(agents): add multi-tool agent skills and commit message guide` |
| **커밋 번호 (SHA)** | `4ccdc4d` (full: `git rev-parse 4ccdc4d`) |
| **짧은 SHA** | `4ccdc4d` |
| **브랜치** | `feature/docs` |
| **부모 커밋** | `a07f092` |

## 2. 주 커밋 내용

- 커밋 메시지 언어 규칙 문서화 (제목 영어 / 본문·바닥글 한국어)
- `.agents` 공통 스킬 허브 추가
- `.grok` `.claude` `.gemini` `.Codex` `.git_Copilot` `.antigravity` `.cursor` 어댑터 추가
- branchs TEMPLATE / plan Git 전략 문서에 규칙 반영

## 3. 상세 내용

### 3.1 배경 / 목적
에이전트·사람이 동일한 커밋 규칙과 프로젝트 컨벤션을 따르도록 스킬/가이드를 고정한다.

### 3.2 변경 범위
- 추가: `.agents/`, 도구별 폴더, `docs/guidance/commit-message.md`, `.github/copilot-instructions.md`
- 수정: `docs/branchs/*`, `docs/README.md`, `LOGIC_AND_GIT_BRANCH_STRATEGY.md`, 루트 `README.md`

### 3.3 기술 포인트
- 공통 정본은 `.agents/SKILL.md`
- 도구 폴더는 얇은 어댑터로 정본을 가리킴
- Claude 폴더는 올바른 철자 `.claude` 사용

### 3.4 의도적으로 하지 않은 것
- 각 SaaS 도구 계정 연동 설정
- pre-commit hook 강제

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 파일 추가 및 feature/docs 커밋
- 결과: Grok 스킬 `cutnkeep` 경로 등록 가능

### 4.2 부작용 / 리스크
- 도구마다 읽는 파일명이 다름 → 어댑터 유지 필요

### 4.3 후속 작업
- develop 병합
- 선택: commit-msg git hook

### 4.4 관련 문서
- `docs/guidance/commit-message.md`
- `.agents/SKILL.md`
