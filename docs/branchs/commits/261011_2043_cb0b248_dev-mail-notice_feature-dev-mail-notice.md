# 메일이 실제로 안 나가는 개발 모드를 화면이 알려 주고 로컬 SMTP 설정 도구 추가 / `cb0b248ee4c66ec1d2941bce0608c26b33dd8df3`

> 브랜치: `feature/dev-mail-notice`  
> 작성일: `2026-10-11 20:43`  
> 작성자: `agent`  
> 파일명: `261011_2043_cb0b248_dev-mail-notice_feature-dev-mail-notice.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(auth): 메일이 실제로 안 나가는 개발 모드를 화면이 알려 주고 로컬 SMTP 설정 도구 추가` |
| **커밋 번호 (SHA)** | `cb0b248ee4c66ec1d2941bce0608c26b33dd8df3` |
| **짧은 SHA** | `cb0b248` |
| **브랜치** | `feature/dev-mail-notice` |
| **부모 커밋** | `c8ac22b` |

## 2. 주 커밋 내용

- 가입 신청 · 재발송 응답에 `mail_delivered` — SMTP 미설정(개발 모드)이면 false
- 인증 화면이 "메일이 실제로 가지 않았다 · 일련번호는 서버 로그의 [DEV MAIL]" 안내
- `scripts/set_smtp_local.sh` — 이 PC 의 .env 에 SMTP 설정

## 3. 상세 내용

### 3.1 배경 / 목적
사용자가 `limjinheng@naver.com` 으로 가입했는데 인증번호가 안 왔다. 원인: 서버가 아니라 **이 PC 의 개발 백엔드(localhost:8000)** 로 가입했고, 그 .env 에 SMTP_HOST 가 없어 메일이 `backend/logs` 에만 `[DEV MAIL · SMTP 미설정]` 으로 남았다. Gmail 만 되도록 막은 것이 아니다(서버는 어떤 수신 주소든 발송).

### 3.2 변경 범위
- 수정: `schemas/auth.py`, `routers/auth.py`, `SignupPage`, `SignupVerifyPage`, `types/index.ts`, 테스트, `docs/guidance/auth.md`
- 추가: `scripts/set_smtp_local.sh`

### 3.3 기술 포인트
- 발신 계정(SMTP_USER)과 수신 주소(To)는 별개 — 수신 주소 제한 코드는 없다
- 앱 비밀번호는 채팅 · 저장소 밖에서 사용자가 직접 입력

### 3.4 의도적으로 하지 않은 것
- 서버 SMTP 비밀번호를 로컬 .env 로 복사 (비밀 값 이동)
- 개발 모드에서 일련번호를 화면에 직접 표시 (운영에서 위험)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 496 · 프런트 vitest 87 · tsc 통과

### 4.2 부작용 / 리스크
- 로컬 백엔드를 다시 시작해야 새 안내가 보임

### 4.3 후속 작업
- 병합 지시 후 develop · main 병합, 서버 재배포
