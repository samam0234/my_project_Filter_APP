# feature/docker-mariadb-data → develop 병합 (no-ff) / `ddb9046dda9e75504efc07015fe7f82b8b1b6b68`

> 브랜치: `develop`  
> 작성일: `2026-10-04 02:44`  
> 작성자: `agent`  
> 파일명: `261004_0244_ddb9046_merge-docker-mariadb-data_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/docker-mariadb-data into develop (no-ff)` |
| **커밋 번호 (SHA)** | `ddb9046dda9e75504efc07015fe7f82b8b1b6b68` |
| **짧은 SHA** | `ddb9046` |
| **브랜치** | `develop` |
| **부모 커밋** | `be11bf1` (develop), `2dc2b22` (feature tip) |

## 2. 주 커밋 내용

- MariaDB 데이터를 호스트 `data/mariaDB_datas` 에 bind mount (`ecc478d`)

## 3. 상세 내용

### 3.1 배경 / 목적

DB 파일을 탐색기에서 보고 백업·이전하기 쉽게 한다.

### 3.2 변경 범위

- `docker-compose.yml`, `.gitignore`, 관련 문서 9개
- 기록: `261004_0244_ecc478d_mariadb-bind-mount_feature-docker-mariadb-data.md`

### 3.3 기술 포인트

- `git merge --no-ff`, 충돌 없음

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과

- `docker compose config` 유효. 컨테이너 기동은 Docker Desktop 이 꺼져 있어 미실시

### 4.2 부작용 / 리스크

- 기존 Docker 이름 볼륨의 데이터는 새 설정에서 보이지 않음 (이전 절차: `docker/mariadb/README.md`)

### 4.3 후속 작업

- Docker Desktop 기동 후 `up` 으로 `data/mariaDB_datas` 생성 확인

### 4.4 관련 문서

- `docker/mariadb/README.md`
