# feature/auth → develop 병합 (no-ff) / `c78b81e177f0495e2686b311cec404d07d9340fa`

> 브랜치: `develop`
> 작성일: `2026-09-30 05:03`
> 작성자: `agent`
> 파일명: `260930_0503_c78b81e_merge-auth_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/auth into develop (no-ff)` |
| **커밋 번호 (SHA)** | `c78b81e177f0495e2686b311cec404d07d9340fa` |
| **짧은 SHA** | `c78b81e` |
| **브랜치** | `develop` |
| **부모 커밋** | `a329466` (develop), `5ef162a` (feature tip) |

## 2. 주 커밋 내용

- 계정 API (`f8677b0`) · 계정 화면 (`3e968a9`) · 계정 문서 (`391b612`)
- 접근 정책 (`35a27db`) · 콘솔 전용 API 전환 (`38a1a3b`) · 회원 전용 화면 게이트 (`b0f75fc`)

## 3. 상세 내용

### 3.1 배경 / 목적

계정 기능(로그인 · 회원가입 · 아이디/비밀번호 찾기)과 접근 정책(비로그인 다운로드만 · 회원 전용 기록/피드백/배치 ·
콘솔 loopback), 이를 반영한 문서를 통합 라인 develop 에 넣는다. 순서: feature/auth → feature/docs-access.

### 3.2 변경 범위

- `backend/app/` (auth · access · console · upload · jobs · feedback · batch · models · db)
- `frontend/src/` (auth 페이지 · RequireLogin · 스토어 · 작업실/기록/배치/홈)
- `console/src/api/client.ts`, `tests/unit/{conftest,test_auth,test_access}.py`
- 기록: `260930_0444_f8677b0…`, `260930_0444_3e968a9…`, `260930_0446_391b612…`, `260930_0459_35a27db…`, `260930_0459_38a1a3b…`, `260930_0500_b0f75fc…`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 충돌 없음 (feature/docs-access 는 feature/auth 끝에서 분기)

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 두 병합 후 develop 에서 pytest 164개 통과, `npm run build` 통과

### 4.2 부작용 / 리스크

- 백엔드 재시작 시 기존 DB 에 `users`·`auth_sessions`·`auth_codes` 생성, `jobs.user_id`·`batch_jobs.user_id` 추가 (자동)
- 소유자 없는 기존 작업(18건)은 사용자 앱에서 보이지 않고 콘솔에서만 조회
- 콘솔은 백엔드와 같은 PC 에서만 전체 조회 가능

### 4.3 후속 작업

- (선택) `git push origin develop` 및 feature 브랜치
- 배포 전: `SECRET_KEY` · `SMTP_*` · `SESSION_COOKIE_SECURE=true` (`docs/web_management/pre-deploy.md`)

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`, `docs/guidance/auth.md`
