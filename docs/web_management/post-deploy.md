# Post-deploy Checks

1. `GET /health` → ok + dialect
2. 사용자 업로드 1건 성공
3. `GET /api/v1/jobs` 에 반영
4. (선택) console에서 Job 확인
5. 로그: `docker compose -p cut_and_keep logs --tail 100`

6. 외부 점검: `python scripts/deploy_check.py remote https://<도메인>` → 실패 0 · 경고 0
7. Cloudflare 를 쓰면: `https://<worker>/health` · `/account` · `/signup/verify` 가 200, 화면 번들 이름이 서버와 같은지
8. 메일: 가입 신청 1건 → 서버 로그 `메일 발송` 확인, 받은편지함 도착
9. `GET /api/v1/llm/models` → `enabled/reachable` (PC Ollama 터널이 켜져 있어야 `true`)

이상 시 `docs/repeater/` 검색.
