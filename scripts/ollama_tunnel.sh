#!/bin/bash
# 내 PC 의 Ollama(11434)를 서버가 쓸 수 있게 SSH 역방향 터널을 열어 둔다 — 끊기면 자동으로 다시 연결한다.
#
#   CNK_SSH_KEY=D:/ssh/CutnKeep/ssh-key-2026-10-10.key CNK_SSH_HOST=ubuntu@168.110.17.193 bash scripts/ollama_tunnel.sh
#
# - PC 에서 Ollama 가 켜져 있어야 한다 (모델은 PC 에 있는 것을 그대로 쓴다: gemma4:e4b · gemma4:12b · qwen3.8:27b)
# - 이 창을 닫거나 PC 가 꺼지면 서버는 키워드 파서(LLM_FALLBACK=heuristic)로 계속 동작한다
# - 서버 쪽 끝은 서버 loopback(127.0.0.1:11435)이라 밖에서는 보이지 않는다 (docker-compose.pc-ollama.yml 의 다리가 backend 에 전달)
# - 개인키는 읽기만 하고 어디에도 출력하지 않는다
set -u
KEY="${CNK_SSH_KEY:?CNK_SSH_KEY 에 SSH 개인키 파일 경로를 넣어 주세요}"
HOST="${CNK_SSH_HOST:?CNK_SSH_HOST 에 ubuntu@서버IP 를 넣어 주세요}"
LOCAL_PORT="${OLLAMA_LOCAL_PORT:-11434}"
REMOTE_PORT="${OLLAMA_REMOTE_PORT:-11435}"

if ! curl -s -m 5 "http://127.0.0.1:${LOCAL_PORT}/api/tags" >/dev/null; then
  echo "이 PC 의 Ollama(${LOCAL_PORT})에 연결되지 않습니다. Ollama 를 먼저 켜 주세요." >&2
  exit 1
fi
echo "Ollama 터널 시작: PC:${LOCAL_PORT} → ${HOST} loopback:${REMOTE_PORT}  (Ctrl+C 로 종료)"
while true; do
  ssh -i "$KEY" -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -o ConnectTimeout=20 \
      -N -R "127.0.0.1:${REMOTE_PORT}:127.0.0.1:${LOCAL_PORT}" "$HOST"
  echo "$(date '+%H:%M:%S') 터널이 끊겼습니다. 5초 뒤 다시 연결합니다…" >&2
  sleep 5
done
