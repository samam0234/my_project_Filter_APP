# API Smoke

> Windows Git Bash 의 curl 은 한글 필드를 깨뜨려 보낼 수 있다 (`docs/find_debug/2026-09-29.md` Issue 1).
> 한글 프롬프트·이름은 Swagger `/docs` · 브라우저 · Python 으로 확인한다.

```bash
curl http://localhost:8000/health

# 비로그인 업로드 — 저장 없이 data URL 결과
curl -F "file=@sample.jpg" -F "prompt=person remove background" http://localhost:8000/api/v1/upload

# 로그인 (쿠키 저장) → 업로드 → 내 작업
curl -c jar.txt -H "Content-Type: application/json" \
     -d '{"username":"tester_01","password":"cutkeep2026"}' http://localhost:8000/api/v1/auth/login
curl -b jar.txt -F "file=@sample.jpg" -F "prompt=person remove background" http://localhost:8000/api/v1/upload
curl -b jar.txt http://localhost:8000/api/v1/jobs
```

기대:
- health: `status=ok`
- 비로그인 upload: `saved=false`, `after_url` 이 `data:image/…`, `backend/data/uploads/` 에 새 폴더 없음
- 비로그인 `GET /api/v1/jobs`: **401**
- 로그인 upload: `saved=true`, `before_url`/`after_url` 이 `/api/v1/files/…`
- 로그인 jobs: 방금 job 포함, 다른 계정으로는 404
