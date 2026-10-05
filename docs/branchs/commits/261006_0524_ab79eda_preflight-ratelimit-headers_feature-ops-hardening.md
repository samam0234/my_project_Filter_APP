# 배포 설정 점검·업로드 속도 제한·보안 헤더 / `ab79eda97d80b2ccafe771170bfafc4cbb4b3cb2`

> 브랜치: `feature/ops-hardening`  
> 작성일: `2026-10-06 05:24`  
> 작성자: `agent`  
> 파일명: `261006_0524_ab79eda_preflight-ratelimit-headers_feature-ops-hardening.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(security): 배포 설정 점검·업로드 속도 제한·보안 헤더` |
| **커밋 번호 (SHA)** | `ab79eda97d80b2ccafe771170bfafc4cbb4b3cb2` |
| **짧은 SHA** | `ab79eda` |
| **브랜치** | `feature/ops-hardening` |
| **부모 커밋** | `12cf0d4` (feature/experiments) |

## 2. 주 커밋 내용

- `core/preflight.py`: production 에서 위험한 설정이면 기동 거부 + CLI 점검
- `core/ratelimit.py`: 업로드 분당 제한 (비로그인 IP 6 · 회원 20)
- 보안 헤더 미들웨어

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 점검 6번 (보안·운영) — Oracle Cloud 백엔드 배포(보류 중인 1번) 전에 "설정 실수로 위험하게 뜨는 것"과
"비로그인 공개 업로드 남용"을 막는다. 지금까지는 `.env.example` 에 "배포 시 수동"으로만 적혀 있었다.

### 3.2 변경 범위

- 추가: `backend/app/core/{preflight,ratelimit}.py`, `tests/unit/{test_preflight,test_ratelimit}.py`
- 수정: `backend/app/{core/config.py, main.py, routers/upload.py}`, `tests/unit/conftest.py`,
  `.env.example`, `docs/{API_DOCUMENTATION.md, web_management/pre-deploy.md}`

### 3.3 기술 포인트

- 개발 환경에서는 같은 항목을 경고로만 (로컬 기본값은 정상)
- 속도 제한은 프로세스 메모리 슬라이딩 윈도우 — 워커 1개 기준. reverse proxy 뒤에서는 `--proxy-headers` 필요 (문서화)
- HSTS 는 `SESSION_COOKIE_SECURE=true`(HTTPS)일 때만 — 로컬 http 에 박히면 브라우저가 계속 https 로 감
- 테스트가 실제 `.env`·CI 환경변수에 영향받던 부분을 명시값으로 고정

### 3.4 의도적으로 하지 않은 것

- Redis 기반 분산 속도 제한 (워커·서버 1대 전제)
- 콘솔 로그인 (loopback 제한 유지, 원격은 앞단 인증)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `APP_ENV=production` + 현재 `.env` → error 4건(SECRET_KEY·DEBUG·SESSION_COOKIE_SECURE·SMTP_HOST)으로 exit 1
- [x] 안전한 값 → "문제 없음" exit 0
- [x] 비로그인 3번째 업로드(제한 2) → 429 + Retry-After
- [x] pytest 전체 통과 (신규 12건)

### 4.2 부작용 / 리스크

- 지금 `.env` 그대로 `APP_ENV=production` 으로 바꾸면 서버가 뜨지 않음 (의도) — 배포 전에 값 교체
- 같은 공유기(NAT) 뒤 여러 비로그인 사용자는 IP 하나로 묶여 제한을 함께 씀

### 4.3 후속 작업

- 프론트 테스트·CI (같은 브랜치 다음 커밋)

### 4.4 관련 문서

- `docs/web_management/pre-deploy.md`
