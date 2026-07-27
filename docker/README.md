# Docker assets

Root `docker-compose.yml` orchestrates:

- `backend` — FastAPI
- `frontend` — Nginx + static build
- `redis` — Phase 2 queue

Optional compose overrides and Nginx extras can live here.

```bash
# from repo root
cp .env.example .env
docker compose up --build
```
