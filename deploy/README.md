# deploy — 배포 부속 파일

> 서버 Compose 밖에서 쓰는 배포 자산. 지금은 사용자 앱 화면을 **Cloudflare Worker**로 내보내는 파일이 있다.

서버 쪽 배포(Compose · HTTPS · PC Ollama)는 [`docker/`](../docker/README.md)에, 전체 순서는 [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)에 있다.

| 경로 | 용도 |
|------|------|
| [cloudflare/worker.js](./cloudflare/worker.js) | Worker 코드 — `/api/*` · `/health`를 백엔드 서버로 그대로 넘긴다 |
| [cloudflare/wrangler.jsonc](./cloudflare/wrangler.jsonc) | Worker 설정 — 이름 `cutnkeep-front`, 정적 파일 위치, 원본 서버 주소(`ORIGIN`) |
| [cloudflare/set_edge_secret.sh](./cloudflare/set_edge_secret.sh) | 비밀 값 `EDGE_SECRET`을 서버 `.env`와 Worker secret에 **같은 값으로 숨겨** 저장 |

---

## 1. 왜 Cloudflare Worker인가

```text
사용자 ─▶ cutnkeep-front.limjinheng0120.workers.dev
            ├─ 정적 화면 (frontend/dist)          ← Cloudflare 엣지에서 바로
            └─ /api/* · /health ─▶ https://168-110-17-193.sslip.io (Caddy → nginx → backend)
```

- 화면 파일은 Cloudflare 엣지가 주고, 서버는 API만 받는다.
- 화면과 API가 **같은 주소**로 보이므로 로그인 쿠키가 그대로 동작한다 (CORS 쿠키 문제가 없다).
- 파일이 없는 주소(`/account` 등)는 `index.html`로 돌려 브라우저 안의 라우터가 처리한다 (`not_found_handling: single-page-application`).
- Worker 코드가 먼저 받는 경로는 `/api/*`와 `/health`뿐이다. 나머지는 정적 파일이다.

### 실제 사용자 IP 전달

서버는 비로그인 속도 제한에 접속 IP를 쓴다. Worker를 거치면 접속 IP가 Cloudflare가 되므로, 실제 IP를 따로 넘긴다.

1. Worker가 `X-Cnk-Real-IP`에 사용자 IP(`CF-Connecting-IP`)를, `X-Cnk-Edge`에 `EDGE_SECRET`을 싣는다. 사용자가 직접 넣은 같은 이름의 헤더와 `X-Real-IP`는 지운다.
2. 서버의 Caddy는 `X-Cnk-Edge`가 `EDGE_SECRET`과 **같을 때만** 그 IP를 믿고, 두 헤더를 지운 뒤 백엔드에 넘긴다 ([`docker/caddy/Caddyfile`](../docker/caddy/Caddyfile)).
3. `EDGE_SECRET`이 비어 있으면 Worker는 500을 돌려주고, Caddy의 이 경로는 꺼진다.

---

## 2. 배포

```bash
# 1) 화면 빌드 — 운영자 표시값은 서버 .env 의 OPERATOR_* 와 같게
cd frontend
VITE_OPERATOR_NAME="컷앤킵 운영자" VITE_OPERATOR_EMAIL="<문의 메일>" VITE_POLICY_DATE="2026-10-11" npm run build

# 2) Worker 배포 (npx wrangler login 이 되어 있어야 한다)
cd ../deploy/cloudflare
npx wrangler deploy

# 3) 점검 — 실패 0 · 경고 0
cd ../.. && python scripts/deploy_check.py remote https://168-110-17-193.sslip.io
```

- **비밀 값은 직접 쓰지 않는다.** `EDGE_SECRET`은 `bash deploy/cloudflare/set_edge_secret.sh`를 사용자가 직접 실행해 서버와 Worker에 같은 값으로 넣는다. 저장소 · 채팅 · 로그에 남기지 않는다.
- 배포 뒤 서버와 Worker의 화면 번들 이름(`assets/index-*.js`)이 같은지, Worker 주소의 `/health`가 200인지, `/api/v1/llm/models`가 `reachable: true`인지 확인한다.
- 서버에서 빌드된 화면을 그대로 쓰려면 frontend 컨테이너의 `/usr/share/nginx/html`을 `frontend/dist`로 가져와 배포해도 된다 (두 번들 이름이 자동으로 같아진다).
- 자체 도메인으로 바꾸면 `wrangler.jsonc`의 `ORIGIN`과 화면의 운영자 표기를 같이 바꾼다.

### 한계

Cloudflare를 거치면 약 **100초**에서 응답이 끊긴다 (524). 27b, 모델을 막 바꾼 12b, 긴 영상과 GIF는 서버 직접 주소(약 300초)가 여유가 있다. 화면은 이 경우를 안내만 한다.

같은 Cloudflare 계정의 `vidshare-front` · `vidshare-console`은 **이 프로젝트가 아니다.** 건드리지 않는다.

---

## 관련 문서

- [`docs/guidance/cloudflare-deploy.md`](../docs/guidance/cloudflare-deploy.md) — 자세한 순서와 이유
- [`docs/HANDOVER.md`](../docs/HANDOVER.md) — 운영 구성 · 접근 방법
- [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) — 공개 배포 전체 순서
