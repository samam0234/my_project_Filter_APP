# Backend ↔ MariaDB

현재 구성: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md) · [`docker/mariadb/README.md`](../../docker/mariadb/README.md)

## 환경

| 위치 | 설정 |
|------|------|
| Docker **backend** | compose 강제: `DB_DIALECT=mariadb`, `MARIADB_HOST=mariadb`, `PORT=3306` |
| 호스트 DBeaver | `127.0.0.1` + `.env` `MARIADB_PORT` (예 3309) + 비밀번호 |
| Adminer | http://localhost:8081 · Server=`mariadb` |

인증: **비밀번호만** (GSS/SSL 끄기). 공식 `mariadb:11`.

## 정상 로그 (backend)

```text
DB 엔진 준비됨 dialect=mysql
DB 테이블 확인/생성 완료 dialect=mysql
… db=mysql …
```

## 실패 시 체크

1. `docker compose -p cut_and_keep ps` — mariadb **healthy**
2. `.env` 의 USER/PASSWORD/DATABASE 와 볼륨 최초 생성 시 값 일치 (불일치 시 `down -v`)
3. 호스트 접속 시 Host 는 **`127.0.0.1`**, Port 는 **`MARIADB_PORT`** (컨테이너 3306 아님)
4. GSS-API exception → 클라이언트 설정 문제. 서버 장애 아님
5. `172.18.0.x` 를 Host 로 쓰지 말 것

## 검증

```powershell
curl http://localhost:8000/health
docker exec cut_and_keep-mariadb-1 mariadb --skip-ssl -uadmin -p... cutnkeep -e "SELECT 1"
```
