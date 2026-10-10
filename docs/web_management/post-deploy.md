# Post-deploy Checks

1. `GET /health` → ok + dialect
2. 사용자 업로드 1건 성공
3. `GET /api/v1/jobs` 에 반영
4. (선택) console에서 Job 확인
5. 로그: `docker compose -p cut_and_keep logs --tail 100`

이상 시 `docs/repeater/` 검색.
