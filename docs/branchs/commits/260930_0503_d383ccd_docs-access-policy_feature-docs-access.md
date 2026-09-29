# 접근 정책(비로그인 다운로드만·회원 전용) 반영 문서 전면 갱신 / `d383ccd9c1e9f9d7183b1ddfc0f19af5fa14a7c5`

> 브랜치: `feature/docs-access`  
> 작성일: `2026-09-30 05:03`  
> 작성자: `agent`  
> 파일명: `260930_0503_d383ccd_docs-access-policy_feature-docs-access.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 접근 정책(비로그인 다운로드만·회원 전용) 반영 문서 전면 갱신` |
| **커밋 번호 (SHA)** | `d383ccd9c1e9f9d7183b1ddfc0f19af5fa14a7c5` |
| **짧은 SHA** | `d383ccd` |
| **브랜치** | `feature/docs-access` |
| **부모 커밋** | `5ef162a` (feature/auth tip) |

## 2. 주 커밋 내용

- 접근 정책 표를 API 문서·계정 가이드에 추가 (비로그인 / 회원)
- 작업·파일·피드백·배치 API 에 권한 명시, `mine` 파라미터 설명 제거, Console API 섹션 신설
- 데이터 흐름을 로그인/비로그인 분기로 재작성
- 콘솔 문서: 콘솔 전용 API · loopback 제한 · `CONSOLE_ALLOW_REMOTE`
- 검증·배포 체크리스트, 디버그 기록(작업 기록 500 원인) 갱신

## 3. 상세 내용

### 3.1 배경 / 목적

`feature/auth` 에서 접근 정책이 바뀌었다 (`35a27db`·`38a1a3b`·`b0f75fc`).
"작업 ID 를 알면 누구나 볼 수 있다", "내 작업만(?mine=1)", "콘솔은 /api/v1/jobs" 등
이전 설명이 문서 곳곳에 남아 있어 전부 찾아 맞췄다.

### 3.2 변경 범위 (24개 파일)

| 분류 | 파일 |
|------|------|
| 재작성 | `docs/Architecture/data-flow.md`, `docs/guidance/api-usage.md`, `docs/vaildates/api-smoke.md`, `docs/vaildates/console-checklist.md` |
| API · 가이드 | `docs/API_DOCUMENTATION.md`, `docs/guidance/{auth,console-admin,user-frontend}.md` |
| 계획 · 구조 | `docs/plan/{CURRENT_STACK,DATABASE,LOGIC_STRUCTURE}.md`, `docs/Architecture/apps.md`, `docs/WORKFLOW.md` |
| 운영 · 검증 | `docs/web_management/pre-deploy.md`, `docs/vaildates/mvp-checklist.md`, `docs/find_debug/{2026-09-29,README}.md` |
| 폴더 README · 루트 | `frontend/README.md`, `backend/README.md`, `console/README.md`, `tests/README.md`, `RUN.md`, `AGENTS.md`, `.env.example` |

### 3.3 기술 포인트

- 접근 정책 표 하나를 API 문서·계정 가이드에 같은 내용으로 두어 어긋나지 않게 함
- 재검색으로 옛 표현 0건 확인: `mine=`, `내 작업만`, `작업 ID 를 알면 누구나`, `인증/권한은 Phase 1`
- api-smoke 에 Git Bash curl 한글 주의 (find_debug Issue 1·8)

### 3.4 의도적으로 하지 않은 것

- `docs/branchs/commits/` 과거 기록 수정

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 구조 테스트 통과, 옛 표현 재검색 0건

### 4.2 부작용 / 리스크

- 없음 (문서만)

### 4.3 후속 작업

- develop 병합: feature/auth → feature/docs-access

### 4.4 관련 문서

- `docs/guidance/auth.md` 1.1 접근 정책
- `docs/API_DOCUMENTATION.md` 접근 정책 한눈에
