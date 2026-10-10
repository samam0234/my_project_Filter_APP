# 로그인·회원가입·계정 찾기 화면 추가 / `3e968a9c6c104b1c13d3ff8b3cb6726dfeaa983e`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 04:44`
> 작성자: `agent`
> 파일명: `260930_0444_3e968a9_auth-pages_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(frontend): 로그인·회원가입·계정 찾기 화면 추가` |
| **커밋 번호 (SHA)** | `3e968a9c6c104b1c13d3ff8b3cb6726dfeaa983e` |
| **짧은 SHA** | `3e968a9` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `f8677b0` |

## 2. 주 커밋 내용

- `/login` · `/signup` · `/find-id` · `/find-password`(2단계)
- 헤더 계정 메뉴, 작업 기록 "내 작업만", 작업실 비로그인 안내
- `useAuthStore` (앱 시작 시 `/auth/me`), axios `withCredentials`

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청: 로그인 · 회원가입 · 아이디/비밀번호 찾기.
로그인은 선택 기능으로 두고(기존 사용 흐름 유지), 로그인 상태의 작업을 사용자와 연결해 "내 작업"을 모아 보게 한다.
SMTP 가 아직 없어 메일은 설정 시 발송, 미설정(로컬) 시 서버 로그에만 남긴다.

### 3.2 변경 범위

- 추가: `src/store/useAuthStore.ts`, `src/components/auth/AuthForm.tsx`, `src/pages/auth/{Login,Signup,FindId,FindPassword}Page.tsx`
- 수정: `App.tsx`, `api/client.ts`, `types/index.ts`, `hooks/useApi.ts`, `components/layout/AppLayout.tsx`,
  `pages/HistoryPage.tsx`, `pages/StudioPage.tsx`

### 3.3 기술 포인트

- 토큰은 HttpOnly 쿠키라 JS 에 없음 → 상태는 `/auth/me` 결과만 보관
- 로그인 상태에서 로그인·가입·찾기 화면 접근 시 `next`(또는 홈)로 이동
- `safeNext`: `/` 로 시작하고 `//` 가 아닌 경로만 허용 (오픈 리다이렉트 방지)
- 입력 규칙은 백엔드 정규식과 동일, 최종 판정은 서버. `autocomplete` 속성으로 비밀번호 관리자 호환
- 비밀번호 재설정 성공 시 서버가 모든 세션을 끊으므로 스토어도 guest 로 전환 후 `/login?reset=1`

### 3.4 의도적으로 하지 않은 것

- 가입 이메일 소유 확인 · 소셜 로그인 · 회원 탈퇴 · 로그인 상태 비밀번호 변경
- 작업 상세·결과 파일 접근 제한 (작업 ID 로 누구나 조회 — 기존 동작 유지)
- 콘솔(:5174) 관리자 인증, IP 단위 속도 제한
- 새 의존성 (passlib · PyJWT · react-router 등)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 전체 154개 통과 (계정 22개 포함)
- [x] `npm run build` (tsc -b + vite) 통과
- [x] 실서버 + Vite 프록시: 가입 → HttpOnly 쿠키 → me → 로그아웃(서버 세션 폐기) → 잘못된 비밀번호 401 →
      로그인 → 아이디 찾기(로그에 DEV MAIL) → 코드 요청 → 로그에서 코드 확인 → 재설정 → 옛 비밀번호 401 · 새 비밀번호 200
- [x] 로그인 상태 업로드 → `jobs.user_id` 연결 · `?mine=true` 조회
- [x] 기존 SQLite 에 `jobs.user_id` ALTER 자동 추가, users·auth_sessions·auth_codes 생성
- [x] headless Chrome: 로그인·회원가입·아이디 찾기·비밀번호 찾기 화면, 로그인 후 헤더·내 작업만
- 검증용 계정·작업·업로드 파일은 확인 후 삭제

### 4.2 부작용 / 리스크

- 새로고침 직후 잠깐 `loading` 상태(헤더 자리표시) — `/auth/me` 응답 대기

### 4.3 후속 작업

- develop 병합
- 배포 전: `SECRET_KEY` 교체 · `SMTP_*` 설정 · HTTPS 에서 `SESSION_COOKIE_SECURE=true`
- 위 3.4 항목

### 4.4 관련 문서

- `docs/guidance/auth.md`
- `docs/API_DOCUMENTATION.md` Auth 섹션
