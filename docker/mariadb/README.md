# MariaDB Docker (비밀번호 전용 · GSS/SSL 없음)

로컬 개발용. **GSS-API(Kerberos)·SSL 은 사용하지 않습니다.**

## 구성

| 항목 | 내용 |
|------|------|
| 이미지 | 공식 `mariadb:11` |
| 인증 | `.env` 의 `MARIADB_USER` / `MARIADB_PASSWORD` 비밀번호만 |
| SSL | `conf.d/99-local.cnf` → `skip_ssl=1` |
| GSS | 플러그인 로드·dual auth 없음 |

## 접속

### Adminer (권장)

http://localhost:8081  

| 항목 | 값 |
|------|-----|
| System | MySQL |
| Server | `mariadb` |
| Username / Password / Database | `.env` 의 `MARIADB_*` |

### DBeaver

| 항목 | 값 |
|------|-----|
| Driver | **MariaDB** |
| Host | `127.0.0.1` |
| Port | `.env` `MARIADB_PORT` (예: 3309) |
| User / Password | `.env` 값 |
| SSL | **끔** |
| Kerberos / GSS / Windows credentials | **끔** |

`172.18.0.x` 는 Docker 브리지 게이트웨이 — 호스트로 쓰지 말 것.

## 데이터 위치

DB 파일은 호스트 **`data/mariaDB_datas/`** 에 저장됩니다 (compose bind mount → 컨테이너 `/var/lib/mysql`).

- 탐색기에서 보이고, 폴더째 복사해 백업·이전할 수 있습니다
- **git 에 올라가지 않습니다** (`.gitignore`) — 폴더는 처음엔 비어 있어야 하며 `.gitkeep` 도 두지 않습니다
- 폴더가 없으면 Docker 가 만듭니다. 컨테이너가 도는 중에 파일을 직접 건드리지 마세요
- 백업은 `down` 으로 멈춘 뒤 폴더를 복사하거나, 켜 둔 채 `mariadb-dump` (아래)

```powershell
docker exec cut_and_keep-mariadb-1 mariadb-dump -uroot -p<MYSQL_ROOT_PASSWORD> cutnkeep > backup.sql
```

## 계정 변경 후 · 초기화

`.env` 의 `MYSQL_*` / `MARIADB_*` 는 **데이터 폴더가 비어 있을 때 처음 한 번만** 적용됩니다.
계정을 바꾸거나 DB 를 비우려면 데이터 폴더를 지웁니다.

> bind mount 라서 `docker compose down -v` 로는 **지워지지 않습니다.**

```powershell
docker compose -p cut_and_keep down
Remove-Item -Recurse -Force data\mariaDB_datas     # DB 데이터 폴더 삭제 = 초기화
docker compose -p cut_and_keep --env-file .env up -d --build
```

## 이전 Docker 볼륨(`cut_and_keep_mariadb_data`)에서 옮기기

예전 설정은 Docker 이름 볼륨에 저장했습니다. 그 데이터를 새 폴더로 옮기려면 (옮길 데이터가 없으면 건너뜀):

```powershell
# 1) 옛 설정(볼륨)이 아직 떠 있을 때 덤프
docker exec cut_and_keep-mariadb-1 mariadb-dump -uroot -p<MYSQL_ROOT_PASSWORD> --all-databases > old.sql
# 2) 새 설정으로 교체 후 기동 (data/mariaDB_datas 가 비어 있어야 함)
docker compose -p cut_and_keep down
docker compose -p cut_and_keep --env-file .env up -d mariadb
# 3) 복원
Get-Content old.sql | docker exec -i cut_and_keep-mariadb-1 mariadb -uroot -p<MYSQL_ROOT_PASSWORD>
# 4) 옛 볼륨 정리 (확인 후)
docker volume rm cut_and_keep_mariadb_data
```

## 컨테이너 내부 확인

```powershell
docker exec cut_and_keep-mariadb-1 mariadb -uadmin -pYOUR_PASSWORD cutnkeep -e "SELECT 1"
```
