# HTTPS 로 공개하기 (Caddy)

공개 서버에서는 `docker-compose.https.yml` 을 겹쳐 띄운다. 앞단의 **Caddy** 가 인증서를 자동으로 받고(Let's Encrypt), 갱신하고,
http 를 https 로 돌린다. 기본 compose 는 그대로 두고 덧붙이기만 한다.

```
인터넷 ──443/80──▶ caddy (인증서 · https) ──▶ frontend nginx (보안 헤더 · /api 프록시) ──▶ backend
                                              (밖으로 포트 없음)
```

## 1. 준비

| 할 일 | 확인 |
|-------|------|
| 도메인 구입 · DNS 의 **A 레코드**를 서버 공인 IP 로 | `nslookup cutnkeep.example.com` 이 서버 IP |
| 서버 방화벽 · 공유기에서 **80 · 443** 열기 | 인증서 발급에 80 이 필요하다 |
| `.env` 작성 | 아래 |

```env
DOMAIN=cutnkeep.example.com
ACME_EMAIL=you@example.com                       # 인증서 만료 알림
CORS_ORIGINS=https://cutnkeep.example.com
APP_ENV=production                               # 위험한 기본값이 남아 있으면 기동 거부 (preflight)
DEBUG=false
SECRET_KEY=...                                   # 32자 이상 난수
SMTP_HOST=...                                    # 메일 — docs/guidance/auth.md 4절
OPERATOR_NAME=... · OPERATOR_EMAIL=... · POLICY_DATE=...   # 개인정보 처리방침 · 약관 (docs/guidance/legal.md)
```

`SESSION_COOKIE_SECURE=true` 는 https compose 가 backend 에 자동으로 넣는다.

## 2. 띄우기

```powershell
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml up -d --build
docker compose -p cut_and_keep -f docker-compose.yml -f docker-compose.https.yml logs -f caddy   # "certificate obtained successfully"
```

- https://도메인 으로 접속 → 자물쇠 표시
- http://도메인 → https 로 이동
- 인증서 · 계정 키는 `data/caddy/` (git 제외). 지우면 다시 발급받는다 — Let's Encrypt 는 같은 도메인 발급 횟수 제한이 있으니 자주 지우지 않는다

## 3. 로컬에서 미리 확인

`DOMAIN=localhost`(기본)로 띄우면 Caddy 가 **자체 서명 인증서**를 만든다. 브라우저 경고는 정상이다.

```powershell
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml up -d --build
curl -kI https://localhost        # -k: 자체 서명 인증서 허용
curl -I http://localhost          # 308 → https
```

## 4. 바뀌는 것

| 항목 | 기본 compose | https compose |
|------|--------------|---------------|
| 공개 포트 | frontend :80 | caddy :80 · :443 (frontend 는 밖으로 안 열림) |
| 인증서 | 없음 | Let's Encrypt 자동 발급 · 갱신 (localhost 는 자체 서명) |
| 세션 쿠키 | `Secure` 꺼짐 | `Secure` 켜짐 + HSTS |
| 실제 접속 IP | nginx 가 본 주소 | Caddy → nginx(`real_ip`) → backend(`TRUSTED_PROXIES`) — 비로그인 처리 횟수 제한이 사람마다 |

## 5. 되돌리기 · 주의

- https compose 없이 다시 띄우면 기본(http :80)으로 돌아간다. 단 HSTS 를 받은 브라우저는 180일 동안 https 로만 가려 한다 — 도메인을 바꾸거나 http 로 돌아갈 계획이면 Caddyfile 의 HSTS 줄을 먼저 지운다
- 영상 · GIF 업로드 한도 · 대기 시간은 nginx(85MB · 600초)가 정한다. Caddy 는 기본으로 크기 · 시간 제한이 없다
- 다른 웹서버가 80 · 443 을 쓰고 있으면 Caddy 가 뜨지 않는다

관련: [security.md](./security.md) · [docker-run.md](./docker-run.md) · [`docker/caddy/Caddyfile`](../../docker/caddy/Caddyfile)
