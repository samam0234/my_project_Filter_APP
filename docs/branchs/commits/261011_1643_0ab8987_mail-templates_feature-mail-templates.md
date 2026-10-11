# 메일을 HTML 템플릿으로 꾸미고 아이디·비밀번호 찾기 메일 보완 / `0ab8987635b906a7dbe8f22e81787907a834fb13`

> 브랜치: `feature/mail-templates`  
> 작성일: `2026-10-11 16:43`  
> 작성자: `agent`  
> 파일명: `261011_1643_0ab8987_mail-templates_feature-mail-templates.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(mail): 메일을 HTML 템플릿으로 꾸미고 아이디·비밀번호 찾기 메일 보완` |
| **커밋 번호 (SHA)** | `0ab8987635b906a7dbe8f22e81787907a834fb13` |
| **짧은 SHA** | `0ab8987` |
| **브랜치** | `feature/mail-templates` |
| **부모 커밋** | `4468283` |

## 2. 주 커밋 내용

- 메일 본문 HTML 템플릿 3종 (아이디 안내 · 비밀번호 재설정 · 회원가입 인증) + 일반 텍스트 대체 본문
- 메일 버튼 주소를 요청 화면 주소(CORS_ORIGINS 허용 목록 안)로 — Cloudflare 화면에서 요청해도 맞게 열림
- 아이디 찾기 안내 문구 보완

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시: 아이디 · 비밀번호 찾기 메일이 안 온다 → 보완, 메일 내용을 세련되게. 점검 결과 SMTP 와 발송은 정상(서버 로그 "메일 발송")이었고, 시도 시점에 서버가 502 였을 가능성이 커서 안내 문구도 함께 보완.

### 3.2 변경 범위
- 추가: `backend/app/services/mail_templates.py`, `tests/unit/test_mail_templates.py`
- 수정: `mailer.py`, `core/deps.py`, `services/auth_service.py`, `routers/auth.py`, `FindIdPage.tsx`, `tests/unit/conftest.py`, `docs/guidance/auth.md`

### 3.3 기술 포인트
- 메일 클라이언트는 `<style>` 을 못 읽는다 → table + 인라인 스타일, 버튼은 td 배경색
- 사용자 입력은 html.escape (속성 탈출 방지 테스트 포함)
- `site_url`: 허용 목록 밖 Origin 은 무시해 임의 주소로 속인 메일을 막음

### 3.4 의도적으로 하지 않은 것
- 발송 비동기화 (응답 시간으로 계정 존재 추측 가능성은 기존과 같음)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과 (종료 코드 0), 프런트 vitest 75 · tsc 통과

### 4.2 부작용 / 리스크
- 서버 `CORS_ORIGINS` 에 Cloudflare 화면 주소를 추가해야 버튼이 그 주소로 열림

### 4.3 후속 작업
- `feature/signup-email-verify` (회원가입 이메일 인증)
