# MariaDB 데이터를 data/mariaDB_datas 에 bind mount 로 저장 / `ecc478db2d5bacaf77ef405b8e5ddb3071c297ca`

> 브랜치: `feature/docker-mariadb-data`  
> 작성일: `2026-10-04 02:44`  
> 작성자: `agent`  
> 파일명: `261004_0244_ecc478d_mariadb-bind-mount_feature-docker-mariadb-data.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(docker): MariaDB 데이터를 data/mariaDB_datas 에 bind mount 로 저장` |
| **커밋 번호 (SHA)** | `ecc478db2d5bacaf77ef405b8e5ddb3071c297ca` |
| **짧은 SHA** | `ecc478d` |
| **브랜치** | `feature/docker-mariadb-data` |
| **부모 커밋** | `be11bf1` (develop) |

## 2. 주 커밋 내용

- `docker-compose.yml`: Docker 이름 볼륨 `mariadb_data` → 호스트 `./data/mariaDB_datas:/var/lib/mysql`
- `.gitignore`: `data/mariaDB_datas/` 전체 제외
- 초기화 방식 변경 문서화: `down -v` 로는 지워지지 않으므로 `down` 후 폴더 삭제
- `docker/mariadb/README.md`: 데이터 위치 · 백업 · 이전 볼륨에서 옮기는 절차

## 3. 상세 내용

### 3.1 배경 / 목적

DB 파일이 Docker 내부 볼륨(Windows 에서는 WSL2 가상 디스크)에 있어 탐색기로 보이지 않고
백업·이전이 번거로웠다. 사용자 요청으로 저장소 루트 `data/mariaDB_datas` 에 저장한다.

### 3.2 변경 범위

- 수정: `docker-compose.yml`, `.gitignore`, `RUN.md`, `data/README.md`, `docker/README.md`, `docker/mariadb/README.md`,
  `docs/guidance/docker-run.md`, `docs/plan/{CURRENT_STACK,DATABASE}.md`, `docs/repeater/mariadb-connection.md`

### 3.3 기술 포인트

- `MYSQL_*` 는 데이터 폴더가 비어 있을 때 한 번만 적용 → 계정 변경 시 폴더 삭제 필요
- 폴더에 `.gitkeep` 등 파일이 있으면 MariaDB 초기화가 실패하므로 두지 않음 (Docker 가 자동 생성)
- `.dockerignore` 는 이미 `data` 전체를 제외하므로 backend 이미지 빌드에 영향 없음
- `docker compose config` 로 마운트 해석 확인: `D:\…\data\mariaDB_datas → /var/lib/mysql`

### 3.4 의도적으로 하지 않은 것

- 기존 Docker 볼륨 데이터 자동 이전 (덤프/복원 절차만 문서화)
- 경로 환경변수화 (`MARIADB_DATA_DIR`) — 필요해지면 추가

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `docker compose config` 유효, bind mount 경로 확인
- [ ] 컨테이너 기동 · 데이터 파일 생성 확인 — **Docker Desktop 이 꺼져 있어 미실시**

### 4.2 부작용 / 리스크

- 기존 이름 볼륨(`cut_and_keep_mariadb_data`)의 데이터는 새 설정에서 보이지 않음 — Docker MariaDB 로 쌓은 데이터가 있으면 이전 절차 필요
- Windows 드라이브 bind mount 는 Docker 볼륨보다 DB 속도가 느리거나 드물게 권한 오류가 날 수 있음
  (오류 시 `docker/mariadb/README.md` 참고, 운영 Linux 서버는 해당 없음)
- 컨테이너가 도는 중 폴더를 직접 건드리면 DB 손상 위험

### 4.3 후속 작업

- Docker Desktop 켠 뒤 `up` → `data/mariaDB_datas` 에 `ibdata1` 등 생성 확인, 백엔드 `DB_DIALECT=mariadb` 연결 확인

### 4.4 관련 문서

- `docker/mariadb/README.md`, `docs/plan/CURRENT_STACK.md`
