# docker — Compose 보조 자산

루트 `docker-compose.yml` 이 스택을 오케스트레이션한다.

**프로젝트 이름:** `cut_and_keep`  
**현재 구성 스냅샷:** [`docs/plan/CURRENT_STACK.md`](../docs/plan/CURRENT_STACK.md)

## 서비스

| 서비스 | 이미지/빌드 | 호스트 포트 |
|--------|-------------|-------------|
| backend | `backend/Dockerfile` (context=루트) | 8000 |
| frontend | `frontend/Dockerfile` | 80 |
| mariadb | 공식 `mariadb:11` | `${MARIADB_PORT}` (예 3309)→3306 |
| redis | `redis:7-alpine` | 6380→6379 |
| adminer | `adminer:4` | 8081 |

## MariaDB (비밀번호 전용)

- 설정: `docker/mariadb/conf.d/99-local.cnf` (`skip_ssl`)
- 초기화: `docker/mariadb/initdb.d/01-password-only.sh`
- 안내: [`docker/mariadb/README.md`](./mariadb/README.md)
- **GSS 커스텀 이미지·SSL 요구 없음**

## 실행

```powershell
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초
docker compose -p cut_and_keep --env-file .env up -d --build
docker compose -p cut_and_keep ps
```

중지(데이터 유지) / 볼륨 포함 삭제:

```powershell
docker compose -p cut_and_keep down
docker compose -p cut_and_keep down -v
```

## 제외

- Console 웹 → Compose 없음, 로컬 `:5174`
- Celery worker → Phase 2
- 구 프로젝트명 `cutnkeep` 스택과 동시 기동 금지
