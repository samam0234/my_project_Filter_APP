# HTTPS(Caddy 자동 인증서), 메일 465 SSL · 개발용 Mailpit · 테스트 발송, 개인정보 처리방침 · 이용약관 · 가입 동의 / `d60674946a677e7a9844910d15035e246368dabe`

> 브랜치: `feature/deploy-https-mail-policy`  
> 작성일: `2026-10-09 08:38`  
> 작성자: `agent`  
> 파일명: `261009_0838_d606749_https-mail-legal_feature-deploy-https-mail-policy.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): HTTPS(Caddy 자동 인증서), 메일 465 SSL · 개발용 Mailpit · 테스트 발송, 개인정보 처리방침 · 이용약관 · 가입 동의` |
| **커밋 번호 (SHA)** | `d60674946a677e7a9844910d15035e246368dabe` |
| **짧은 SHA** | `d606749` |
| **브랜치** | `feature/deploy-https-mail-policy` |
| **부모 커밋** | `0e2698e` |

## 2. 주 커밋 내용

- HTTPS: `docker-compose.https.yml` + `docker/caddy/Caddyfile` — 인증서 자동 발급·갱신, http→https, HSTS, Server 헤더 숨김, frontend 외부 포트 제거, Secure 쿠키
- Caddy 뒤 실제 IP: nginx `include /etc/nginx/snippets/*.conf` + `docker/nginx/realip-behind-caddy.conf`
- 메일: `SMTP_SSL`(465), Date · Message-ID, `scripts/send_test_mail.py`, Mailpit(프로필 mail)
- `/privacy` · `/terms` 화면, 운영자 정보 빌드 인자(`OPERATOR_*`)
- 가입 [필수] 만 14세 · 약관 · 방침 동의 — 서버 검사 + `users.terms_agreed_at`

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "HTTPS(인증서), 메일(SMTP) 설정, 개인정보 처리방침과 이용약관 진행".

### 3.2 변경 범위
- 추가: compose https 오버레이, Caddyfile, nginx realip 조각, `send_test_mail.py`, 프론트 `pages/legal/*` · `data/legal.ts` · 가입 테스트, 문서 `https-deploy.md` · `legal.md`
- 수정: mailer · config · 사용자 모델/스키마/서비스/저장소/라우터(동의), 세션 마이그레이션 컬럼, compose(Mailpit · 빌드 인자), 프론트 Dockerfile · nginx · App · 레이아웃 · 가입 화면 · 스토어 · 클라이언트, 테스트 가입 요청 7곳, 문서(auth · user-frontend · FEATURES · security · pre-deploy · 색인)

### 3.3 기술 포인트
- https 모드에서 frontend 는 Docker 네트워크에서만 접근 가능 → nginx 가 Docker 대역의 X-Real-IP 를 믿어도 안전 (기본 모드에는 넣지 않음)
- 동의는 화면만이 아니라 서버도 검사 (API 직접 호출 차단), 예전 회원은 동의 시각 NULL
- 방침 문구는 실제 동작(보관 24시간 · 비로그인 미저장 · 문장만 학습 · 외부 AI 는 문장만)과 대응표로 관리 (`legal.md`)

### 3.4 의도적으로 하지 않은 것
- 법률 검토(초안으로 명시), 회원 스스로 탈퇴 화면, 법정대리인 동의 절차, 실제 SMTP 계정 연결(사용자 계정 필요)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 411 · 프론트 53 통과
- [x] Docker https 모드: `https://localhost` 200(자체 서명), `http` 308, HSTS · CSP, Set-Cookie `Secure`, 동의 없는 가입 400, Mailpit 수신(한글 제목 정상), 테스트 계정 삭제

### 4.2 부작용 / 리스크
- 기존 API 클라이언트가 `agree_terms` 없이 가입하면 400 (의도)
- HSTS 를 받은 브라우저는 180일간 https 로만 접속

### 4.3 후속 작업
- 서비스 DB MariaDB 전환 · 백업 · 모델 받기

### 4.4 관련 문서
- `docs/guidance/https-deploy.md`, `docs/guidance/legal.md`, `docs/guidance/auth.md`
