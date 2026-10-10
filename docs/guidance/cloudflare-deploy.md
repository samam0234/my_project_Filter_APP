# 프런트엔드를 Cloudflare 에 올리기

> 화면(정적 파일)은 Cloudflare Worker 가 서비스하고, `/api/*` · `/health` 는 같은 Worker 가 백엔드 서버로 넘긴다.
> 브라우저는 화면과 API 를 같은 주소로 보므로 **로그인 쿠키 · CORS 설정을 바꿀 필요가 없다**.
> 서버 쪽 HTTPS 설정은 [https-deploy.md](./https-deploy.md), 전체 순서는 [../DEPLOYMENT.md](../DEPLOYMENT.md).

```text
브라우저 ── https://cutnkeep-front.<계정>.workers.dev ──┬─ 화면 (frontend/dist, SPA)
                                                       └─ /api/* · /health ─▶ Worker ─▶ https://<서버 도메인> (Caddy → nginx → backend)
```

## 구성 파일

| 파일 | 역할 |
|------|------|
| `deploy/cloudflare/wrangler.jsonc` | Worker 이름 · 정적 파일 폴더(`frontend/dist`) · SPA 처리 · `ORIGIN`(서버 주소) |
| `deploy/cloudflare/worker.js` | `/api/*` · `/health` 를 서버로 전달. 사용자 IP 와 비밀 값을 헤더로 실어 보냄 |
| `deploy/cloudflare/set_edge_secret.sh` | 비밀 값 `EDGE_SECRET` 을 서버 `.env` 와 Worker 에 같은 값으로 저장 |
| `frontend/public/_headers` | 정적 파일 응답의 보안 헤더(CSP 등 — nginx 와 같은 값) |
| `docker/caddy/Caddyfile` | 비밀 값이 맞는 요청만 `X-Cnk-Real-IP` 를 실제 사용자 IP 로 믿는다 |

## 왜 비밀 값(EDGE_SECRET)이 필요한가

서버의 속도 제한(비로그인 분당 6회)은 접속 IP 기준이다. Worker 를 거치면 서버는 Cloudflare 의 IP 만 보게 되어
**모든 사용자가 한 사람처럼 제한**된다. Worker 가 실제 사용자 IP 를 헤더로 전달하고, Caddy 는
`EDGE_SECRET` 이 맞을 때만 그 헤더를 믿는다 (밖에서 헤더만 위조해 IP 를 속일 수 없게). 서버에 `EDGE_SECRET` 이 비어 있으면 이 경로는 꺼진다.

## 올리는 순서

```bash
# 1) 빌드 (운영자 표시값은 서버 .env 의 OPERATOR_* 와 같게)
cd frontend && VITE_OPERATOR_NAME="운영자 이름" VITE_OPERATOR_EMAIL="문의 메일" VITE_POLICY_DATE="2026-10-11" npm run build
# 2) Worker 배포 (처음이면 npx wrangler login)
cd ../deploy/cloudflare && npx wrangler deploy
# 3) 비밀 값 저장 + 서버 Caddy 재시작 (처음 한 번 — 저장소 루트, Git Bash)
CNK_SSH_KEY=<개인키 경로> CNK_SSH_HOST=ubuntu@<서버IP> bash deploy/cloudflare/set_edge_secret.sh
```

서버에 Caddy 설정(`docker/caddy/Caddyfile` · `docker-compose.https.yml`)이 반영돼 있어야 한다 (`git pull` 후 `up -d caddy`).

## 확인

- `https://cutnkeep-front.<계정>.workers.dev/` 화면, `/account` 새로고침(SPA 이동), `/health` 가 `{"status":"ok"…}`
- 가입 · 로그인이 되고 새로고침해도 유지되는지, 비로그인으로 연속 7번째 처리가 429 인지(IP 별 제한)

## 알아 둘 것

- 서버 주소를 바꾸면(자체 도메인) `wrangler.jsonc` 의 `ORIGIN` 만 바꾸고 다시 `wrangler deploy`
- 화면을 고칠 때마다 1~2번을 다시 한다. 서버(`frontend` 컨테이너)의 화면도 그대로 살아 있다
- 오래 걸리는 요청(영상 · GIF, 큰 해석 모델의 첫 호출)이 Worker 를 거치며 끊기는지는 실제 요청으로 확인한다
- 운영 콘솔(`console/`)은 이 Worker 에 올리지 않았다 — 공개하려면 Cloudflare Access 같은 접근 제한이 먼저 필요하다
