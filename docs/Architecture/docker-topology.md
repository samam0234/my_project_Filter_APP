# Docker Topology (`cut_and_keep`)

Compose project: **`cut_and_keep`**  
Network: **`cut_and_keep_net`**  
스냅샷: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

```text
cut_and_keep-frontend-1   :80
cut_and_keep-backend-1    :8000  → mariadb:3306, redis:6379
cut_and_keep-mariadb-1    :${MARIADB_PORT:-3306}→3306  (예 3309)
cut_and_keep-redis-1      :6380→6379
cut_and_keep-adminer-1    :8081→8080  (default server=mariadb)
```

## Images

| 이름 | 비고 |
|------|------|
| `cut_and_keep-backend` | context=저장소 루트, `requirements.docker.txt` |
| `cut_and_keep-frontend` | nginx + 정적 빌드 |
| `mariadb:11` | 공식 이미지, password-only, skip_ssl |
| `redis:7-alpine` | |
| `adminer:4` | DB UI |

**제외:** GSS 커스텀 MariaDB 이미지 (`cut_and_keep-mariadb:gssapi` 등) · Celery

## Backend 환경 오버라이드 (컨테이너)

| 키 | 값 |
|----|-----|
| `DB_DIALECT` | `mariadb` |
| `MARIADB_HOST` | `mariadb` |
| `MARIADB_PORT` | `3306` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `LLM_BASE_URL` | `host.docker.internal:11434` (기본) |

호스트 도구용 `.env` 의 `MARIADB_HOST=localhost` / `MARIADB_PORT=3309` 와 **역할이 분리**된다.

## Notes

- Docker Desktop Images 목록은 전역 — 다른 프로젝트 이미지도 보일 수 있음
- 프로젝트 격리는 컨테이너·네트워크·볼륨 prefix (`cut_and_keep_*`)
- Console 은 Compose 미포함
