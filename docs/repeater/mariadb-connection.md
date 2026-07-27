# Backend ↔ MariaDB

## 환경
`DB_DIALECT=mariadb`, `MARIADB_HOST=mariadb` (compose network)

## 정상 로그
```
DB engine ready dialect=mysql
DB tables ensured dialect=mysql
```

## 실패 시 체크

1. mariadb healthcheck 통과 여부
2. 환경변수 user/password/database 일치
3. 호스트에서 접속 시 `localhost:3306` (컨테이너 외부)

## 검증
```bash
curl http://localhost:8000/health
# db_dialect: mysql
```
