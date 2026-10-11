# 서버에서 Ollama 쓰기 — 내 PC 의 모델을 연결

> Oracle Cloud 서버(ARM · GPU 없음 · 24GB)에는 모델을 따로 받지 않는다. **내 PC 에서 돌고 있는 Ollama**(gemma4:e4b · gemma4:12b · qwen3.8:27b)를
> SSH 역방향 터널로 서버에 연결해 쓴다. 서버가 CPU 로 12b · 27b 를 돌리면 문장 하나에 몇 분이 걸리지만, PC 의 GPU 로는 수 초~수십 초다.

```text
사용자 ─▶ Cloudflare/Caddy ─▶ nginx ─▶ backend ─▶ ollama-bridge(172.18.0.1:11434) ─▶ 서버 loopback 11435
                                                                                          ▲ SSH 역방향 터널 (PC 가 연결)
                                                          내 PC 의 Ollama (11434) ──────────┘
```

## 켜는 순서

1. **PC**: Ollama 를 켠다 (`ollama list` 에 모델이 있어야 한다).
2. **PC**: 터널을 연다 — 이 창이 열려 있는 동안 서버가 PC 의 Ollama 를 쓴다. 끊기면 5초마다 다시 연결한다.
   ```bash
   CNK_SSH_KEY=<개인키 경로> CNK_SSH_HOST=ubuntu@<서버IP> bash scripts/ollama_tunnel.sh
   ```
3. **서버**(한 번만):
   ```bash
   sudo iptables -I INPUT 5 -s 172.18.0.0/16 -p tcp --dport 11434 -j ACCEPT && sudo netfilter-persistent save   # docker 네트워크에서만 허용
   # .env
   LLM_PROVIDER=ollama
   LLM_FALLBACK=heuristic                       # PC 가 꺼져 있으면 키워드 파서로 계속 동작
   DOCKER_LLM_BASE_URL=http://172.18.0.1:11434  # cut_and_keep_net 게이트웨이 (docker network inspect cut_and_keep_net)
   docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.pc-ollama.yml up -d ollama-bridge backend
   ```
4. 확인: `curl https://<서버>/api/v1/llm/models` → `"enabled":true,"reachable":true`, 모델마다 `available`

## 보안

- 터널의 서버 쪽 끝은 **서버 loopback(127.0.0.1:11435)** 이라 밖에서 보이지 않는다. 다리(`ollama-bridge`)는 docker 네트워크 주소에만 귀를 열고, 방화벽도 그 대역만 허용한다.
- Ollama API 에는 인증이 없다. 서버 컨테이너(backend)만 닿을 수 있게 위 구성을 유지하고, 터널 포트를 `0.0.0.0` 으로 열지 않는다.
- 사용자의 처리 요청이 **내 PC 의 GPU** 를 쓴다. 비로그인 분당 6회 · 회원 20회 제한(`UPLOAD_RATE_*`)이 그대로 걸린다.

## 알아 둘 것 (측정값: 2026-10-11, RTX 4070 SUPER 12GB)

| 모델 | 서버 직접 주소 | 비고 |
|------|----------------|------|
| e4b | 사진 1장 약 10~35초 | 모델이 이미 올라와 있으면 짧다 (해석 약 7초 + 세그 약 3초) |
| 12b | 약 60~95초 | 다른 모델이 올라와 있으면 바꿔 올리느라 길다 |
| 27b | 약 180초 | VRAM 이 모자라 일부가 CPU 로 돈다 — 첫 호출이 가장 길다 |

- **Cloudflare 주소는 응답을 100초까지만 기다린다**(무료 플랜 한계, 524). 27b · 모델 교체 직후의 12b 는 이 주소에서 끊길 수 있다 → 화면이 안내를 보여 준다. 서버 직접 주소(`https://<서버 도메인>`)는 300초까지 기다린다.
- 모델 바꿈 지연을 줄이려면 PC 에서 `OLLAMA_KEEP_ALIVE=30m` 로 모델을 오래 올려 둔다.
- 터널이 끊기면(PC 꺼짐 · 절전 · 네트워크) 해석이 키워드 파서로 떨어진다. 사진 처리는 계속되지만 복잡한 문장(위치 · 색 · 순서)은 덜 정확하다. 작업실의 모델 상자는 모델이 "미적용"으로 바뀐다.
- 터널 창이 닫혀도 서버는 멈추지 않는다. PC 를 켤 때마다 `ollama_tunnel.sh` 를 다시 켜면 된다 (Windows 시작 프로그램에 넣어도 된다).
