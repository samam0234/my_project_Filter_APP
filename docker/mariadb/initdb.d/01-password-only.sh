#!/bin/bash
# 볼륨 최초 생성 시 1회 — 비밀번호 전용 계정 확인 (GSS/SSL 없음)
# MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE 는 공식 entrypoint 가 이미 생성함.
set -euo pipefail

ROOT_PASS="${MYSQL_ROOT_PASSWORD:-rootpass}"
APP_USER="${MYSQL_USER:-cutnkeep}"
APP_PASS="${MYSQL_PASSWORD:-cutnkeep}"
APP_DB="${MYSQL_DATABASE:-cutnkeep}"

# root@% 원격 접속 (Adminer/DBeaver 호스트 포트 매핑용)
mariadb -uroot -p"${ROOT_PASS}" <<SQL
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${ROOT_PASS}';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- 앱 유저: 비밀번호만 (gssapi / auth_socket 등 사용 안 함)
CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASS}';
GRANT ALL PRIVILEGES ON \`${APP_DB}\`.* TO '${APP_USER}'@'%';

FLUSH PRIVILEGES;
SQL

echo "[initdb] password-only users ready: ${APP_USER}@%, root@% (no GSS, no SSL)"
