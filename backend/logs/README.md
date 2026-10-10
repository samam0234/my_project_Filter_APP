# backend/logs — 백엔드 앱 로그

FastAPI 백엔드의 loguru 파일 로그가 쌓인다. 콘솔(stderr) 출력과 같은 내용이다.

| 파일 | 내용 |
|------|------|
| `app_YYYY-MM-DD.log` | 하루 단위 로그 (자정 회전, UTF-8) |

- 보관: `LOG_RETENTION_DAYS` (기본 14일) 지나면 자동 삭제
- 레벨: `DEBUG=true` → DEBUG, 아니면 INFO
- 학습·스크립트 로그는 루트 [`logs/`](../../logs/README.md)

```env
LOG_DIR=logs
LOG_RETENTION_DAYS=14
```

Docker: `./backend/logs` → `/app/logs` 마운트.
