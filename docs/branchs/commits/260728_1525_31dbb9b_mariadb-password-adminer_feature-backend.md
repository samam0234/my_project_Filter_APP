# MariaDB 비밀번호 전용 구성과 Adminer 연동 / `31dbb9b`

> 브랜치: `feature/backend`  
> 작성일: `2026-07-28 15:25`  
> 작성자: `while`  
> 파일명: `260728_1525_31dbb9b_mariadb-password-adminer_feature-backend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(docker): MariaDB 비밀번호 전용 구성과 Adminer 연동` |
| **커밋 번호 (SHA)** | `31dbb9bfdc3587adab3c8dfcc47f7694cf5630ce` |
| **짧은 SHA** | `31dbb9b` |
| **브랜치** | `feature/backend` |
| **부모 커밋** | `256c2b6` |

## 2. 주 커밋 내용

- 공식 `mariadb:11` 사용 (GSS 커스텀 이미지 제거)
- 서버 SSL 비활성 (`skip_ssl`) · 비밀번호(`mysql_native_password`)만 사용
- `.env` 계정·`MARIADB_PORT`(예: 3309)·root 비밀번호를 compose에 주입
- backend 컨테이너: Redis `redis:6379`, LLM `host.docker.internal` 오버라이드
- Adminer `:8081` 추가, `docker/mariadb` conf·init·README 추가

## 3. 상세 내용

### 3.1 배경 / 목적
DBeaver GSS-API 예외·호스트/컨테이너 DB 주소 혼선·포트 충돌을 줄이고, 로컬 Docker에서 안정적인 비밀번호 접속과 데이터 영속을 맞춘다.

### 3.2 변경 범위
- 추가: `docker/mariadb/README.md`, `conf.d/99-local.cnf`, `initdb.d/01-password-only.sh`
- 수정: `docker-compose.yml`, `.env.example`
- 삭제: 없음 (이전 GSS Dockerfile 은 워킹트리에서 제거 후 미커밋 상태였음)

### 3.3 기술 포인트
- 호스트 DBeaver: `127.0.0.1:${MARIADB_PORT}` / 컨테이너 내부: `mariadb:3306`
- 네트워크 이름 `cut_and_keep_net`, 프로젝트 `-p cut_and_keep`
- `.env` 시크릿은 커밋하지 않음

### 3.4 의도적으로 하지 않은 것
- Kerberos/GSS 실연동 (KDC·keytab 필요)
- develop/main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] Docker 확인 — `cut_and_keep` 스택 healthy, MariaDB 3309, backend `dialect=mysql`
- [x] Adminer / DBeaver 비밀번호 접속 가능
- 결과 서술: jobs/feedbacks/batch_jobs 테이블 생성, 앱 데이터 MariaDB 저장

### 4.2 부작용 / 리스크
- 계정·포트 변경 시 기존 볼륨은 `down -v` 후 재생성 필요
- 로컬 uvicorn + `DB_DIALECT=sqlite` 는 여전히 SQLite 사용

### 4.3 후속 작업
- develop 병합 시 `--no-ff`
- 필요 시 DATABASE.md 포트 예시 동기화

### 4.4 관련 문서
- `docker/mariadb/README.md`
- `docs/plan/DATABASE.md`
