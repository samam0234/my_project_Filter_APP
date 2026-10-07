# 운영 콘솔 관리자 로그인과 리버스 프록시 뒤 무인증 노출 차단 / `afa40336b5289975197b83d2f30da2a3aa2e2610`

> 브랜치: `feature/console-auth`  
> 작성일: `2026-10-07 21:20`  
> 작성자: `agent`  
> 파일명: `261007_2120_afa4033_console-admin-login_feature-console-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(console): 운영 콘솔 관리자 로그인과 리버스 프록시 뒤 무인증 노출 차단` |
| **커밋 번호 (SHA)** | `afa40336b5289975197b83d2f30da2a3aa2e2610` |
| **짧은 SHA** | `afa4033` |
| **브랜치** | `feature/console-auth` |
| **부모 커밋** | `8effede` |

## 2. 주 커밋 내용

- 콘솔 API 가드 `require_local_console` → `require_console` (관리자 로그인 · loopback · 원격 허용 3경로, `ConsoleActor` 반환)
- 설정 `CONSOLE_ADMINS` · `CONSOLE_REQUIRE_LOGIN`, preflight 경고(로그인 미강제 · 관리자 비어 있음)
- `GET /api/v1/console/me`, 검수(단건·일괄) `reviewed_by` 에 `admin:{아이디}`
- 콘솔 로그인 화면(`LoginPage`), 헤더 접속 주체·로그아웃, 401·403 인터셉터 → 로그인 화면, `withCredentials`
- 문서: `console-admin.md`(관리자 로그인 절), `API_DOCUMENTATION.md`(Console 접근 규칙), `.env.example`

## 3. 상세 내용

### 3.1 배경 / 목적
콘솔 API 의 유일한 보호는 "요청 주소가 loopback 인가" 였다. 배포(Oracle Cloud)에서 같은 서버의 nginx 가 프록시하면
uvicorn 이 보는 주소가 127.0.0.1 이 될 수 있어(X-Forwarded-For 미설정 시) **로그인 없이 전체 회원 작업·학습 데이터가 열린다**.
반대로 원격 운영을 하려면 `CONSOLE_ALLOW_REMOTE=true` 로 누구에게나 여는 방법뿐이었다.

### 3.2 변경 범위
- 수정: `backend/app/core/{access,config,preflight}.py`, `backend/app/routers/console.py`,
  `console/src/{App.tsx, api/client.ts, store/useConsoleStore.ts, types/index.ts}`,
  `tests/unit/{test_access,test_batch_api,test_learning_review}.py`, 문서 3개
- 추가: `console/src/pages/LoginPage.tsx`, `LoginPage.test.tsx`

### 3.3 기술 포인트
- 새 테이블·컬럼 없이 설정의 아이디 목록으로 관리자 판정 (마이그레이션 불필요, 아이디는 소문자 저장이라 대소문자 무시)
- 사용자 앱과 같은 로그인 API·세션 쿠키 재사용 — 로그인 잠금·만료 정책이 그대로 적용
- 관리자 아닌 계정으로 로그인하면 콘솔이 즉시 로그아웃 (콘솔 도메인에 일반 회원 세션을 남기지 않음)
- 기존 테스트 기대값 변경: 원격 비로그인 403 → 401, 원격 + 일반 회원 403

### 3.4 의도적으로 하지 않은 것
- users 테이블 role 컬럼(마이그레이션 필요), 관리자 2단계 인증, 감사 로그 테이블

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과, 콘솔 vitest 13 · build 통과

### 4.2 부작용 / 리스크
- 기본값(`CONSOLE_REQUIRE_LOGIN=false`)은 로컬 개발 편의를 위해 기존 동작 유지 — 배포 시 true 로 바꿔야 함 (preflight 경고)

### 4.3 후속 작업
- `feature/console-users` (회원 관리), `feature/console-system` (시스템 상태·정리)

### 4.4 관련 문서
- `docs/guidance/console-admin.md`, `docs/API_DOCUMENTATION.md`
