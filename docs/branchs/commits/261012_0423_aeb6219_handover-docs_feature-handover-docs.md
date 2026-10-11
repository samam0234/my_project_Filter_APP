# 인수인계 문서 추가와 모든 에이전트 지침 갱신, 빠진 문서 보완 / `aeb62195910f456f70172a6193a24094c79371b5`

> 브랜치: `feature/handover-docs`  
> 작성일: `2026-10-12 04:23`  
> 작성자: `agent`  
> 파일명: `261012_0423_aeb6219_handover-docs_feature-handover-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 인수인계 문서 추가와 모든 에이전트 지침 갱신, 빠진 문서 보완` |
| **커밋 번호 (SHA)** | `aeb62195910f456f70172a6193a24094c79371b5` |
| **짧은 SHA** | `aeb6219` |
| **브랜치** | `feature/handover-docs` |
| **부모 커밋** | `5c88a6c` |

## 2. 주 커밋 내용

- `docs/HANDOVER.md` 신규 — 인수인계 정본
- 에이전트 지침 12개 파일에 같은 "인수인계 · 현재 상태" 블록, 낡은 표 갱신
- 빠진 문서 보완 (DB · api-usage · https-deploy · docker/backend/frontend/scripts README · deploy/README)

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시: "모든 에이전트에게 지금까지의 내용을 업데이트해 인수인계 가능하게, 문서에서 부족한 내용은 채우거나 수정".

### 3.2 변경 범위
- 신규: `docs/HANDOVER.md`, `deploy/README.md`
- 수정: `AGENTS.md`, `.agents/**`, `.antigravity/`, `.Codex/`, `.cursor/rules/`, `.gemini/`, `.github/copilot-instructions.md`, `.git_Copilot/`, `.claude/CLAUDE.md`, `.grok/**`, docs 7개, README 5개

### 3.3 기술 포인트
- 비밀 값 · 키 경로 · 서버 계정 정보는 어디에도 적지 않고 "사용자에게서 받는다"로 안내 (저장소는 공개)
- 인수인계 블록은 모든 지침에 같은 문구로 넣어 어긋나지 않게 함, 상세는 HANDOVER 한 곳

### 3.4 의도적으로 하지 않은 것
- 과거 기록(vaildates · branchs 의 이전 기록) 수정

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 505 · 프런트 vitest 95 · tsc 통과 (문서 등록 검사 포함)

### 4.2 부작용 / 리스크
- 없음 (문서만)

### 4.3 후속 작업
- 병합 · push
