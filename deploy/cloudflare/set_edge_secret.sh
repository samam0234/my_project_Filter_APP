#!/bin/bash
# Worker ↔ 서버 비밀 값(EDGE_SECRET)을 새로 만들어 두 곳에 같은 값으로 저장한다 (값은 화면에 출력하지 않는다).
#   1) 서버 ~/cutnkeep/.env  2) Cloudflare Worker secret  → 3) 서버 Caddy 재시작
# 실행 (Git Bash, 저장소 루트):  bash deploy/cloudflare/set_edge_secret.sh
# 환경 변수: CNK_SSH_KEY(개인키 경로) · CNK_SSH_HOST(예: ubuntu@168.110.17.193)
set -euo pipefail
KEY="${CNK_SSH_KEY:?CNK_SSH_KEY 에 SSH 개인키 파일 경로를 넣어 주세요}"
HOST="${CNK_SSH_HOST:?CNK_SSH_HOST 에 ubuntu@서버IP 를 넣어 주세요}"
SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes "$HOST")
SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(40))')"

printf '%s\n' "$SECRET" | "${SSH[@]}" 'read -r S; cd ~/cutnkeep && sed -i "/^EDGE_SECRET=/d" .env && printf "EDGE_SECRET=%s\n" "$S" >> .env && chmod 600 .env'
(cd "$(dirname "$0")" && printf '%s' "$SECRET" | npx wrangler secret put EDGE_SECRET)
"${SSH[@]}" 'cd ~/cutnkeep && docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml up -d caddy'
echo "완료 — 서버 .env 와 Worker 에 같은 EDGE_SECRET 을 저장했고 Caddy 를 다시 시작했습니다."
