# Docker Run (`cut_and_keep`)

```bash
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초 1회
docker compose -p cut_and_keep up --build -d
docker compose -p cut_and_keep ps
```

| 서비스 | URL/포트 |
|--------|----------|
| frontend | http://localhost |
| backend | http://localhost:8000 |
| MariaDB | localhost:3306 |
| Redis | localhost:6380 |

중지:

```bash
docker compose -p cut_and_keep down
```

콘솔은 Compose 미포함 → 로컬 `console` 개발 서버 사용.
