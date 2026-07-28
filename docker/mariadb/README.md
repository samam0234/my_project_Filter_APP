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

## 계정 변경 후

볼륨에 옛 계정이 남습니다.

```powershell
docker compose -p cut_and_keep down -v
docker compose -p cut_and_keep --env-file .env up -d --build
```

## 컨테이너 내부 확인

```powershell
docker exec cut_and_keep-mariadb-1 mariadb -uadmin -pYOUR_PASSWORD cutnkeep -e "SELECT 1"
```
