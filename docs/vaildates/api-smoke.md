# API Smoke

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/jobs

# upload (example)
curl -F "file=@sample.jpg" -F "prompt=사람만 남기고 배경 제거" http://localhost:8000/api/v1/upload
```

기대:
- health: `status=ok`
- upload: `job_id`, `before_url`, `after_url`
- jobs: 방금 job 포함
