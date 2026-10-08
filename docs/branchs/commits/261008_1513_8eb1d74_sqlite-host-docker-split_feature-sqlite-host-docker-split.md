# 호스트와 Docker 백엔드가 같은 SQLite 파일을 쓰다 깨지는 문제 — 파일 분리와 기동 시 손상 감지 / `8eb1d7403955a0e2e876558fac5863ea0b9450ff`

> 브랜치: `feature/sqlite-host-docker-split`  
> 작성일: `2026-10-08 15:13`  
> 작성자: `agent`  
> 파일명: `261008_1513_8eb1d74_sqlite-host-docker-split_feature-sqlite-host-docker-split.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(db): 호스트와 Docker 백엔드가 같은 SQLite 파일을 쓰다 깨지는 문제 — 파일 분리와 기동 시 손상 감지` |
| **커밋 번호 (SHA)** | `8eb1d7403955a0e2e876558fac5863ea0b9450ff` |
| **짧은 SHA** | `8eb1d74` |
| **브랜치** | `feature/sqlite-host-docker-split` |
| **부모 커밋** | `d3d9b77` |

## 2. 주 커밋 내용

- 호스트 backend 기본 SQLite 를 `data/cutnkeep.host.db` 로 분리, Docker backend·worker 는 compose 가 `DOCKER_SQLITE_PATH`(기본 `data/cutnkeep.db`)로 명시
- 기동 시 `PRAGMA quick_check` 로 서비스 DB 손상을 감지해 오류 로그로 원인·조치 안내 (`check_sqlite_integrity`)
- `DATABASE.md` 에 분리 이유·손상 복구 절차 추가, RUN·CURRENT_STACK·배포 가이드·`backend/data/README.md` 경로 갱신
- 테스트 4건(`tests/unit/test_sqlite_integrity.py`)

## 3. 상세 내용

### 3.1 배경 / 목적
2026-10-08 Docker 서비스 DB 의 `jobs` 루트 페이지가 OpenCV 경고 텍스트로 덮여 업로드가 전부 500 이 됐다. `backend/data` 가 bind mount 라 호스트 backend 와 Docker backend 가 같은 파일을 번갈아 쓴 것이 유력한 원인이다.

### 3.2 변경 범위
- 추가: `tests/unit/test_sqlite_integrity.py`
- 수정: `backend/app/core/config.py`, `backend/app/db/session.py`, `docker-compose.yml`, `.env.example`, `RUN.md`, `backend/data/README.md`, `docs/plan/{DATABASE,CURRENT_STACK,DEVELOPMENT_AND_DEPLOYMENT_GUIDE}.md`

### 3.3 기술 포인트
- compose 의 `environment` 가 `env_file(.env)` 보다 우선하므로 `.env` 의 `SQLITE_PATH` 가 무엇이든 Docker 는 자기 파일을 쓴다
- 기존 Docker 데이터(복구한 admin 계정)는 `cutnkeep.db` 그대로라 이전이 필요 없다
- 손상 감지는 기동을 막지 않는다 (users 등 읽히는 테이블을 살릴 기회를 남김)

### 3.4 의도적으로 하지 않은 것
- 자동 복구(데이터 판단이 필요해 수동 절차로 문서화), 서비스 DB 를 MariaDB 로 옮기기

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] pytest 375 통과
- [x] Docker backend 재빌드: 컨테이너 `SQLITE_PATH=data/cutnkeep.db`, 손상 경고 없음, 기동 완료
- 로컬 `.env`(git 무시)의 `SQLITE_PATH` 도 `data/cutnkeep.host.db` 로 바꿈

### 4.2 부작용 / 리스크
- 호스트 backend 는 새 빈 DB 로 시작한다 — 호스트에서 쓰던 계정은 Docker 쪽에만 있음

### 4.3 후속 작업
- 배포에서는 서비스 DB 도 MariaDB 로 옮기는 것을 검토

### 4.4 관련 문서
- `docs/plan/DATABASE.md` (호스트와 Docker 는 다른 SQLite 파일 · 손상 복구)
