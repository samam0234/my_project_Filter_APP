# Docker Topology (`cut_and_keep`)

Compose project name: **`cut_and_keep`**

```
cut_and_keep-frontend-1   :80
cut_and_keep-backend-1    :8000  → MariaDB, Redis
cut_and_keep-mariadb-1    :3306
cut_and_keep-redis-1      :6380→6379
```

## Images

- `cut_and_keep-backend` (slim: 루트 `requirements.docker.txt`, build context = 저장소 루트)
- `cut_and_keep-frontend`
- `mariadb:11`, `redis:7-alpine`

## Notes

- Docker Desktop Images 목록은 **전역**이라 다른 프로젝트 이미지도 같이 보임.
- 프로젝트 격리는 컨테이너/네트워크/볼륨 prefix로 한다.
- 콘솔(`console/`)은 현재 Compose에 미포함 — 로컬 `npm run dev` 또는 추후 서비스 추가.
