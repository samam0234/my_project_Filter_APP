# 회원가입 이메일 인증 — 메일의 일련번호로 가입 완료 / `db029dda26aa572832f34db27b6450bf5c123106`

> 브랜치: `feature/signup-email-verify`  
> 작성일: `2026-10-11 16:49`  
> 작성자: `agent`  
> 파일명: `261011_1649_db029dd_signup-email-verify_feature-signup-email-verify.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(auth): 회원가입 이메일 인증 — 메일의 일련번호로 가입 완료` |
| **커밋 번호 (SHA)** | `db029dda26aa572832f34db27b6450bf5c123106` |
| **짧은 SHA** | `db029dd` |
| **브랜치** | `feature/signup-email-verify` |
| **부모 커밋** | `6f3d0b6` |

## 2. 주 커밋 내용

- 가입 신청(`/auth/signup/start`) → 메일의 8글자 일련번호 → 인증(`/auth/signup/verify`) → 가입 완료·로그인
- 메일의 [회원가입 인증] 버튼이 `/signup/verify?email=…` 을 연다 (이메일 미리 채움)
- 일련번호 다시 받기(`/auth/signup/resend`), 화면: 하이픈 자동 입력 · 다시 받기 쿨다운

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시: 가입하기 후 이메일로 사이트가 주는 랜덤 일련번호와 "회원가입 인증" 버튼 → 다음 가입 화면에서 일련번호 입력. 이메일 소유 확인이 없던 `auth.md 7절 후속` 항목을 해결.

### 3.2 변경 범위
- 백엔드: `routers/auth.py`, `services/auth_service.py`, `models/user.py`(SignupPending), `core/passwords.py`, `core/config.py`, `schemas/auth.py`, `services/maintenance.py`
- 프런트: `SignupPage`, `SignupVerifyPage`(신규), `App.tsx`, `api/client.ts`, `store/useAuthStore.ts`
- 문서: API · auth · FEATURES · user-frontend · frontend README · .env.example · 처리방침 화면

### 3.3 기술 포인트
- 인증 전에는 `users` 에 행이 없다 — 신청 정보는 `signup_pending`(비밀번호 해시만)에만, 인증 시 옮기고 삭제
- 일련번호 HMAC(`signup:<email>`) 해시 저장, 시도 횟수 5회, 유효 30분, 재발송 간격 60초
- 인증이 켜져 있으면 `POST /auth/signup` 은 403 — 인증 우회 방지
- 기존 테스트는 conftest 에서 인증을 꺼 두고 인증 흐름은 `test_signup_verify.py` 가 켜서 검증

### 3.4 의도적으로 하지 않은 것
- 기존 회원(예: 운영자 계정)의 이메일 재인증 — 새 가입부터 적용
- 이메일 변경 기능

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 495 통과, 프런트 vitest 84 · tsc 통과
- [x] 메일 HTML 을 실제 브라우저로 렌더링해 데스크톱 · 모바일 확인

### 4.2 부작용 / 리스크
- 서버 `CORS_ORIGINS` 에 Cloudflare 화면 주소가 있어야 메일 버튼이 그 주소로 열린다 (없으면 첫 주소)
- `signup_pending` 은 `create_all` 로 새 테이블이 생김 (기존 테이블은 건드리지 않음)

### 4.3 후속 작업
- 병합 → 서버 배포 → 실제 메일로 가입 확인
