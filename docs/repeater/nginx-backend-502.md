# nginx 가 backend 의 옛 IP 로 접속해 모든 /api 가 502

## 1. 환경
Oracle Cloud 서버 (Docker Compose · Caddy → nginx → backend), 2026-10-11

## 2. 증상
- Cloudflare 화면에서 "서버 연결 안 됨", `/health` · `/api/*` 가 모두 502
- 서버 직접 주소도 502 — Cloudflare 문제가 아니었다
- nginx 로그: `connect() failed (111: Connection refused) while connecting to upstream, upstream: "http://172.18.0.7:8000/..."`

## 3. 원인
`.env` 에 값을 넣자 compose 가 backend 컨테이너를 **다시 만들었고 IP 가 바뀌었다**. nginx 는 시작할 때 `backend` 이름을 한 번만 찾아 옛 IP(172.18.0.7)로 계속 접속했다.

## 4. 해결
- 즉시: `docker compose exec frontend nginx -s reload`
- 재발 방지: `frontend/nginx.conf` 가 Docker DNS(`resolver 127.0.0.11 valid=10s`)로 10초마다 다시 찾도록 변수 `proxy_pass http://$backend_upstream` 사용. backend 를 강제로 다시 만들어도 10초 안에 복구되는 것을 확인

## 5. 검증 명령
```bash
curl -s https://<서버>/health                 # 직접 주소
curl -s https://<worker>.workers.dev/health   # Cloudflare 경유
docker compose -p cut_and_keep up -d --force-recreate --no-deps backend   # 재생성 후에도 10초 안에 200
```

진단 순서: 서버 직접 주소가 502 면 서버 쪽, 직접은 되고 Worker 만 502 면 Worker/`EDGE_SECRET` 쪽 ([cloudflare-deploy.md](../guidance/cloudflare-deploy.md)).
