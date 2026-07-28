# Docker Run (`cut_and_keep`)

현재 구성 요약: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

```powershell
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초 1회 — MARIADB_PORT, 계정, MYSQL_ROOT_PASSWORD 확인
docker compose -p cut_and_keep --env-file .env up -d --build
docker compose -p cut_and_keep ps
```

| 서비스 | URL / 포트 |
|--------|------------|
| frontend (nginx) | http://localhost |
| backend API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| **Adminer** | http://localhost:8081 · Server=`mariadb` |
| MariaDB (호스트) | `127.0.0.1` + `.env` **`MARIADB_PORT`** (예: 3309) |
| Redis (호스트) | localhost:**6380** |

## 인증 · DB

- MariaDB: **비밀번호만** (GSS/SSL 미사용)
- DBeaver: Host `127.0.0.1`, Port=`MARIADB_PORT`, SSL/GSS 끔, 드라이버 MariaDB 권장
- Docker backend 는 compose 가 `mariadb:3306` 으로 붙음 (`.env` 의 localhost 무시)

## 중지

```powershell
docker compose -p cut_and_keep down          # 볼륨 유지
docker compose -p cut_and_keep down -v       # DB 초기화
```

## 참고

- 콘솔(`console/`)은 Compose **미포함** → 로컬 `npm run dev` (:5174)
- 백엔드 이미지: 루트 `requirements.docker.txt` (경량; 가중치 없으면 stub 세그)
- 상세 MariaDB: `docker/mariadb/README.md`
