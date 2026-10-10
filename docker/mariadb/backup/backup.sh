#!/bin/bash
# MariaDB 자동 백업 (compose 서비스 mariadb-backup)
# 서비스 DB(회원 · 작업 · 배치)와 학습 DB(피드백 · 학습 후보)가 같은 데이터베이스에 있어 한 번에 덤프한다.
#   BACKUP_HOURS 마다 /backups/<DB>-YYYYmmdd-HHMMSS.sql.gz, BACKUP_KEEP_DAYS 일이 지난 것은 지운다.
#   덤프가 실패하거나 압축 파일이 깨졌으면 그 파일은 남기지 않는다 (좋은 백업을 밀어내지 않게).
# 복구: docs/plan/DATABASE.md "MariaDB 백업 · 복구"
set -u
set -o pipefail

DB="${MARIADB_DATABASE:-cutnkeep}"
HOURS="${BACKUP_HOURS:-24}"
KEEP="${BACKUP_KEEP_DAYS:-7}"
mkdir -p /backups

while true; do
  ts="$(date +%Y%m%d-%H%M%S)"
  out="/backups/${DB}-${ts}.sql.gz"
  if mariadb-dump --skip-ssl -h "${MARIADB_HOST:-mariadb}" -uroot -p"${MYSQL_ROOT_PASSWORD}" \
       --single-transaction --quick --routines --triggers --databases "${DB}" | gzip -c > "${out}.part" \
     && gzip -t "${out}.part"; then
    mv "${out}.part" "${out}"
    echo "$(date '+%F %T') 백업 완료 ${out} ($(du -h "${out}" | cut -f1))"
  else
    rm -f "${out}.part"
    echo "$(date '+%F %T') 백업 실패 — 다음 주기에 다시 시도" >&2
  fi
  find /backups -name "${DB}-*.sql.gz" -mtime "+$((KEEP - 1))" -delete
  sleep "$((HOURS * 3600))"
done
