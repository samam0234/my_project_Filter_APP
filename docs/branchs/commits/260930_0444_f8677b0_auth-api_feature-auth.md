# 로그인·회원가입·아이디/비밀번호 찾기 API 추가 / `f8677b0a40ea564785559fd7b9c5702ed86da488`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 04:44`
> 작성자: `agent`
> 파일명: `260930_0444_f8677b0_auth-api_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(auth): 로그인·회원가입·아이디/비밀번호 찾기 API 추가` |
| **커밋 번호 (SHA)** | `f8677b0a40ea564785559fd7b9c5702ed86da488` |
| **짧은 SHA** | `f8677b0` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `a329466 (develop)` |

## 2. 주 커밋 내용

- `/api/v1/auth` signup · login · logout · me · find-id · password/request · password/reset
- scrypt 비밀번호 해시, HttpOnly 세션 쿠키(DB 에는 토큰 SHA-256), 로그인 잠금, 재설정 코드(HMAC · 만료 · 시도 · 재발송 간격)
- SMTP 메일러 (미설정 시 로그 기록)
- `jobs.user_id` + `GET /jobs?mine=true`, 업로드 시 소유자 연결
- `init_db` 최소 마이그레이션 (`_ensure_columns`)
- 테스트 22개

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청: 로그인 · 회원가입 · 아이디/비밀번호 찾기.
로그인은 선택 기능으로 두고(기존 사용 흐름 유지), 로그인 상태의 작업을 사용자와 연결해 "내 작업"을 모아 보게 한다.
SMTP 가 아직 없어 메일은 설정 시 발송, 미설정(로컬) 시 서버 로그에만 남긴다.

### 3.2 변경 범위

- 추가: `core/passwords.py`, `core/deps.py`, `models/user.py`, `repositories/user_repository.py`,
  `schemas/auth.py`, `services/auth_service.py`, `services/mailer.py`, `routers/auth.py`, `tests/unit/test_auth.py`
- 수정: `core/config.py`(계정·SMTP 설정), `db/session.py`, `models/__init__.py`, `models/job.py`,
  `repositories/job_repository.py`, `routers/{jobs,router,upload}.py`

### 3.3 기술 포인트

- 계정 존재 추측 방지: 로그인 실패 메시지 동일 + 없는 아이디도 `DUMMY_HASH` 검증, 찾기 API 응답 동일
- SQLite 는 tz 를 버리므로 만료 비교 시 naive → UTC 로 간주 (`_aware`)
- `create_all` 은 기존 테이블 컬럼을 추가하지 않음 → `_ADDED_COLUMNS` 목록만 `ALTER … ADD COLUMN … NULL`
- 테스트는 메모리 SQLite(StaticPool) + `get_db` override + `send_mail` 가로채기, lifespan 미실행

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

- ALTER 로 추가된 `jobs.user_id` 는 기존 DB 에서 FK 제약 없음 → 사용자 삭제 시 값이 남을 수 있음 (새 DB 는 SET NULL)
- 로컬(SMTP 미설정)에서는 인증 코드가 서버 로그에 남음 — 배포 시 SMTP 필수
- 작업 중 사용자 로컬 백엔드(`--reload`)가 멈춰 있었음 (재기동 필요)

### 4.3 후속 작업

- develop 병합
- 배포 전: `SECRET_KEY` 교체 · `SMTP_*` 설정 · HTTPS 에서 `SESSION_COOKIE_SECURE=true`
- 위 3.4 항목

### 4.4 관련 문서

- `docs/guidance/auth.md`
- `docs/API_DOCUMENTATION.md` Auth 섹션
