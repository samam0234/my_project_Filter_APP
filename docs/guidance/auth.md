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

로그인은 **선택**이다. 로그인하지 않아도 작업실에서 처리하고 결과를 내려받을 수 있다.
다만 저장·기록·피드백·배치는 **로그인 회원 전용**이다 (아래 1.1).

### 1.1 접근 정책

| 기능 | 비로그인 | 로그인 회원 |
|------|----------|-------------|
| 작업실 처리 (배경 제거·블러·크롭·지우기) | ✅ 결과를 응답에 담아 **다운로드만** — 서버에 기록·파일·실패 케이스를 남기지 않음 | ✅ 저장 (작업 기록 · 결과 파일 보관) |
| 작업 기록 · 작업 상세 | 🔒 로그인 안내 | ✅ **본인 작업만** |
| 결과 파일 `/files/*` | 🔒 404 | 본인 작업만 |
| 피드백 · 정답 알려주기 | ✖ (저장된 작업이 없음) | ✅ 본인 작업만 |
| 배치 | 🔒 로그인 안내 | ✅ 본인 배치만 조회 |

- 비로그인 업로드: `run_pipeline(persist=False)` → 실패 케이스를 `data/feedback` 에 남기지 않고,
  결과 이미지는 data URL 로 응답한 뒤 `backend/data/uploads/{job_id}` 를 즉시 삭제
- 로그인 업로드: `jobs.user_id` 로 소유자 연결 → 작업 기록(`/history`)에서 모아 본다
- 남의 작업·파일은 `core/access.owned_job` 이 **404** 로 막는다 (존재 여부 비노출)
- 소유자 없는(로그인 기능 이전) 작업은 사용자 앱에서 보이지 않고 **운영 콘솔**에서만 조회
- 운영 콘솔 전체 조회 API(`/api/v1/console/*`)는 서버 PC(loopback) 요청만 허용 (`CONSOLE_ALLOW_REMOTE`)

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
| `CONSOLE_ALLOW_REMOTE` | false | 운영 콘솔 API 원격 허용 (앞단 접근 제어가 있을 때만 true) |

---

## 6. DB

`init_db()` (백엔드 시작 시)가 자동 생성·보강한다.

| 테이블 | 내용 |
|--------|------|
| `users` | id · username · email · display_name · password_hash · failed_logins · locked_until · last_login_at |
| `auth_sessions` | id(=토큰 SHA-256) · user_id · expires_at · user_agent |
| `auth_codes` | user_id · purpose(`password_reset`) · code_hash · attempts · expires_at · used_at |
| `jobs.user_id` | 기존 테이블에 **ALTER 로 추가** (NULL 허용). 비로그인 작업은 저장하지 않으므로, NULL 은 로그인 기능 이전 작업뿐 |
| `batch_jobs.user_id` | 기존 테이블에 ALTER 로 추가. 배치를 등록한 회원 |

사용자를 지우면 세션·코드는 함께 삭제된다. 기존 DB 에 ALTER 로 추가된 `jobs.user_id` 는
외래키 제약 없이 들어가므로, 사용자 삭제 시 작업의 `user_id` 가 남을 수 있다 (새 DB 는 `SET NULL`).

---

## 7. 하지 않은 것 (후속)

- 이메일 소유 확인(가입 시 인증 메일) · 소셜 로그인 · 회원 탈퇴 · 비밀번호 변경(로그인 상태)
- 콘솔(:5174) 관리자 로그인 — 지금은 서버 PC(loopback) 제한으로 대체
- 소유자 없는 옛 작업을 특정 계정에 귀속하는 도구
- 요청 IP 단위 속도 제한 (계정 단위 잠금만 있음)
