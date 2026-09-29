# 계정 기능 가이드와 관련 문서 갱신 / `391b6120fd67893ef6ea94aebe55cb1ebbd94f91`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 04:46`
> 작성자: `agent`
> 파일명: `260930_0446_391b612_auth-docs_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(auth): 계정 기능 가이드와 관련 문서 갱신` |
| **커밋 번호 (SHA)** | `391b6120fd67893ef6ea94aebe55cb1ebbd94f91` |
| **짧은 SHA** | `391b612` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `3e968a9` |

## 2. 주 커밋 내용

- `docs/guidance/auth.md` 신규 (흐름 · 규칙 · 위협별 보안 대응 · SMTP · 설정 · DB · 후속)
- API · DATABASE · CURRENT_STACK · .env.example · frontend/backend/tests README · user-frontend · 체크리스트 · 허브

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청: 로그인 · 회원가입 · 아이디/비밀번호 찾기.
로그인은 선택 기능으로 두고(기존 사용 흐름 유지), 로그인 상태의 작업을 사용자와 연결해 "내 작업"을 모아 보게 한다.
SMTP 가 아직 없어 메일은 설정 시 발송, 미설정(로컬) 시 서버 로그에만 남긴다.

### 3.2 변경 범위

- 추가: `docs/guidance/auth.md`
- 수정: `.env.example`, `docs/API_DOCUMENTATION.md`, `docs/plan/{DATABASE,CURRENT_STACK}.md`, `docs/README.md`,
  `docs/guidance/{README,user-frontend}.md`, `docs/vaildates/mvp-checklist.md`, `frontend/README.md`, `backend/README.md`, `tests/README.md`

### 3.3 기술 포인트

- 배포 전 필수 설정(SECRET_KEY · SMTP · SESSION_COOKIE_SECURE)을 가이드·.env.example·체크리스트 세 곳에 명시
- 로컬 개발에서 코드 확인 방법(`[DEV MAIL` 로그 검색) 안내

### 3.4 의도적으로 하지 않은 것

- 가입 이메일 소유 확인 · 소셜 로그인 · 회원 탈퇴 · 로그인 상태 비밀번호 변경
- 작업 상세·결과 파일 접근 제한 (작업 ID 로 누구나 조회 — 기존 동작 유지)
- 콘솔(:5174) 관리자 인증, IP 단위 속도 제한
- 새 의존성 (passlib · PyJWT · react-router 등)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 구조 테스트 통과, 문서 링크 확인

### 4.2 부작용 / 리스크

- 없음 (문서만)

### 4.3 후속 작업

- develop 병합
- 배포 전: `SECRET_KEY` 교체 · `SMTP_*` 설정 · HTTPS 에서 `SESSION_COOKIE_SECURE=true`
- 위 3.4 항목

### 4.4 관련 문서

- `docs/guidance/auth.md`
- `docs/API_DOCUMENTATION.md` Auth 섹션
