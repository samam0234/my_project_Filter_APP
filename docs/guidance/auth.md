# 계정 가이드 — 로그인 · 회원가입 · 아이디/비밀번호 찾기

코드: `backend/app/routers/auth.py` · `services/auth_service.py` · `core/passwords.py` · `services/mailer.py`
화면: `frontend/src/pages/auth/` · 테스트: `tests/unit/test_auth.py`

---

## 1. 흐름

| 기능 | 화면 | API | 결과 |
|------|------|-----|------|
| 회원가입 | `/signup` | `POST /api/v1/auth/signup` | 계정 생성 + 바로 로그인 |
| 로그인 | `/login?next=…` | `POST /api/v1/auth/login` | 세션 쿠키 발급 |
| 로그아웃 | 헤더 | `POST /api/v1/auth/logout` | 서버 세션 폐기 + 쿠키 삭제 |
| 내 정보 | (앱 시작 시) | `GET /api/v1/auth/me` | 로그인 사용자 / 401 |
| 아이디 찾기 | `/find-id` | `POST /api/v1/auth/find-id` | 가입 이메일로 아이디 발송 |
| 비밀번호 찾기 ① | `/find-password` | `POST /api/v1/auth/password/request` | 아이디+이메일 일치 시 6자리 코드 메일 |
| 비밀번호 찾기 ② | 같은 화면 | `POST /api/v1/auth/password/reset` | 새 비밀번호 저장 + **모든 기기 로그아웃** |

로그인은 **선택**이다. 로그인하지 않아도 작업실은 그대로 쓴다.
로그인 상태로 처리한 작업은 `jobs.user_id` 로 연결되어 작업 기록의 **내 작업만**(`?mine=1`)에서 모아 본다.

---

## 2. 규칙

| 항목 | 규칙 |
|------|------|
| 아이디 | 영문 소문자·숫자·밑줄 4~20자 (대문자로 입력해도 소문자로 저장) |
| 이메일 | 형식 검사, 소문자로 저장, 계정당 1개 · 중복 불가 |
| 비밀번호 | 8~64자, 영문과 숫자 각각 1개 이상 |
| 이름 | 선택, 50자 이하 (헤더 표시용) |

프론트(`components/auth/AuthForm.tsx`)도 같은 규칙으로 즉시 안내하지만 **최종 판정은 서버**다.

---

## 3. 보안 설계

| 위협 | 대응 |
|------|------|
| DB 유출 시 비밀번호 노출 | `hashlib.scrypt` (n=2¹⁴, r=8, p=1) + 사용자별 16바이트 salt. 파라미터를 해시 문자열에 함께 저장 |
| DB 유출 시 세션 탈취 | 세션 토큰 원문은 쿠키에만, DB 에는 SHA-256 |
| XSS 로 토큰 탈취 | 쿠키 `HttpOnly` — JS 에서 읽을 수 없음 (프론트는 `/auth/me` 결과만 보관) |
| CSRF | 쿠키 `SameSite=Lax` — 다른 사이트의 POST 에 쿠키가 실리지 않음 |
| 비밀번호 대입 | 5회 실패 → 10분 잠금 (`LOGIN_MAX_FAILURES`, `LOGIN_LOCK_MINUTES`) |
| 계정 존재 추측 | 로그인 실패 메시지 동일 · 없는 아이디도 더미 해시 검증으로 같은 시간 · 아이디/비밀번호 찾기 응답 항상 동일 |
| 재설정 코드 추측 | 6자리 코드를 HMAC(SECRET_KEY) 로 저장 · 10분 만료 · 5회 틀리면 폐기 · 60초 재발송 간격 · 최신 1개만 유효 · 1회용 |
| 재설정 후 기존 세션 | 비밀번호를 바꾸면 그 계정의 모든 세션 삭제 |
| 로그인 후 외부로 보내기 | `next` 는 `/` 로 시작하는 앱 내부 경로만 허용 |

---

## 4. 메일 (SMTP)

아이디 찾기·재설정 코드는 메일로만 전달한다 (API 응답에 절대 포함하지 않음).

```env
# 배포: 실제 SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=앱 비밀번호
SMTP_FROM=Cut & Keep <you@example.com>
SMTP_STARTTLS=true
```

**`SMTP_HOST` 가 비어 있으면(로컬 기본) 메일을 보내지 않고 서버 로그에 본문을 남긴다.**
개발 중에는 `backend/logs/app_YYYY-MM-DD.log` 에서 `[DEV MAIL` 을 찾아 코드를 확인한다.

```powershell
Select-String -Path backend\logs\app_*.log -Pattern "DEV MAIL" -Context 0,4 | Select-Object -Last 1
```

> 로그에 인증 코드가 남으므로 **배포 환경에서는 반드시 SMTP 를 설정**하고 로그 접근을 제한한다.

---

## 5. 설정

| 환경변수 | 기본 | 설명 |
|----------|------|------|
| `SECRET_KEY` | `dev-secret-change-me` | 재설정 코드 HMAC 키. **배포 시 긴 난수로 교체** (바꾸면 발급된 코드 무효) |
| `SESSION_COOKIE_NAME` | `cnk_session` | |
| `SESSION_TTL_HOURS` | 168 | 로그인 유지 시간 (7일) |
| `SESSION_COOKIE_SECURE` | false | **HTTPS 배포 시 true** (로컬 http 에서 true 면 쿠키가 저장되지 않음) |
| `LOGIN_MAX_FAILURES` · `LOGIN_LOCK_MINUTES` | 5 · 10 | 로그인 잠금 |
| `AUTH_CODE_TTL_MINUTES` · `AUTH_CODE_MAX_ATTEMPTS` · `AUTH_CODE_RESEND_SECONDS` | 10 · 5 · 60 | 재설정 코드 |
| `SMTP_*` | (비움) | 위 4절 |

---

## 6. DB

`init_db()` (백엔드 시작 시)가 자동 생성·보강한다.

| 테이블 | 내용 |
|--------|------|
| `users` | id · username · email · display_name · password_hash · failed_logins · locked_until · last_login_at |
| `auth_sessions` | id(=토큰 SHA-256) · user_id · expires_at · user_agent |
| `auth_codes` | user_id · purpose(`password_reset`) · code_hash · attempts · expires_at · used_at |
| `jobs.user_id` | 기존 테이블에 **ALTER 로 추가** (NULL 허용). 비로그인 작업은 NULL |

사용자를 지우면 세션·코드는 함께 삭제된다. 기존 DB 에 ALTER 로 추가된 `jobs.user_id` 는
외래키 제약 없이 들어가므로, 사용자 삭제 시 작업의 `user_id` 가 남을 수 있다 (새 DB 는 `SET NULL`).

---

## 7. 하지 않은 것 (후속)

- 이메일 소유 확인(가입 시 인증 메일) · 소셜 로그인 · 회원 탈퇴 · 비밀번호 변경(로그인 상태)
- 작업 상세·파일 접근 제한 — 지금은 작업 ID 를 알면 누구나 볼 수 있다 (기존 동작 유지)
- 콘솔(:5174) 관리자 인증
- 요청 IP 단위 속도 제한 (계정 단위 잠금만 있음)
