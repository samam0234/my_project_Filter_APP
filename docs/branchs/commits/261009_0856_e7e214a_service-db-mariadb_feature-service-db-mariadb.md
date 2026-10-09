# Docker 서비스 DB 를 MariaDB 로 전환(옛 SQLite 자동 이전), MariaDB 자동 백업 · 복구 확인 / `e7e214aa0ad2edd80b5884673ad262661ade1955`

> 브랜치: `feature/service-db-mariadb`  
> 작성일: `2026-10-09 08:56`  
> 작성자: `agent`  
> 파일명: `261009_0856_e7e214a_service-db-mariadb_feature-service-db-mariadb.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(db): Docker 서비스 DB 를 MariaDB 로 전환(옛 SQLite 자동 이전), MariaDB 자동 백업 · 복구 확인` |
| **커밋 번호 (SHA)** | `e7e214aa0ad2edd80b5884673ad262661ade1955` |
| **짧은 SHA** | `e7e214a` |
| **브랜치** | `feature/service-db-mariadb` |
| **부모 커밋** | `128ffdb` |

## 2. 주 커밋 내용

- Docker 서비스 DB 기본을 MariaDB 로 (`DOCKER_DB_DIALECT`), 학습 DB 와 같은 데이터베이스
- 옛 SQLite 자동 이전 `app/db/sqlite_import.py` (`SERVICE_DB_IMPORT_FROM`), 수동 실행도 가능
- `mariadb-backup` 서비스 — 매일 덤프 · 7일 보관 · 실패 덤프 버림
- SQLite 백업 임시 이름 · 조각 정리, `.gitattributes` LF 고정
- API 테스트를 MariaDB 테스트 DB 로도 실행하는 선택지(`CNK_TEST_SERVICE_DB_URL`)

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "서비스 DB 를 MariaDB 로 전환", "학습 DB(MariaDB) 백업 자동화". SQLite 는 동시 접속에 약하고 10-08 에 깨진 적이 있다.

### 3.2 변경 범위
- 추가: `backend/app/db/sqlite_import.py`, `docker/mariadb/backup/backup.sh`, `.gitattributes`, `tests/unit/test_service_db_import.py`
- 수정: `config.py`(SERVICE_DB_IMPORT_FROM), `db/session.py`(기동 시 이전), `services/db_backup.py`, `docker-compose.yml`, `tests/unit/conftest.py`, `.gitignore`, `.env.example`, 문서

### 3.3 기술 포인트
- 이전은 대상 회원 · 작업이 0 일 때만 — 이미 쓰는 DB 를 덮지 않음, 같은 기본 키는 건너뜀, 양쪽에 있는 열만
- 백업은 root 로 `--single-transaction`(InnoDB 잠금 없이 일관된 덤프), `gzip -t` 로 압축 확인 뒤에만 이름 확정
- MariaDB 에서도 API 테스트 398개 통과 — 시간대 · 정밀도 문제 없음

### 3.4 의도적으로 하지 않은 것
- 호스트 개발 서버의 기본 DB 는 SQLite 유지, 백업 파일의 외부 복사(운영자 몫)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 414 통과 (+ MariaDB 테스트 DB 로 398 통과)
- [x] Docker: 자동 이전(admin 1 · 세션 5 · 작업 1), `/health` db_dialect=mysql, 백업 생성 → `cutnkeep_test` 로 복구해 행 수 일치

### 4.2 부작용 / 리스크
- SQLite 로 되돌리면 그동안 MariaDB 에 쌓인 데이터는 SQLite 에 없음
- 백업과 원본이 같은 디스크 — 외부 복사 필요

### 4.3 후속 작업
- LaMa 모델 자동 받기, 품질 개선

### 4.4 관련 문서
- `docs/plan/DATABASE.md`
