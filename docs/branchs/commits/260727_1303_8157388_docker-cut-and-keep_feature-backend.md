# cut_and_keep Docker stack / `8157388`

> 브랜치: `feature/backend` → `develop`  
> 작성일: `2026-07-27`  
> 작성자: project

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(docker): add cut_and_keep compose stack with slim backend image` |
| **커밋 번호 (SHA)** | `815738817c847f9ee7b5d8f75b4358784e957030` |
| **짧은 SHA** | `8157388` |
| **브랜치** | `feature/backend`, merge → `develop` (pushed) |
| **부모 커밋** | `8914abe` |

## 2. 주 커밋 내용

- Compose 프로젝트 `cut_and_keep` 으로 스택 기동
- `requirements.docker.txt` 경량 백엔드 이미지
- Redis 호스트 포트 6380 (충돌 회피)
- `db` 패키지 import 오류 수정

## 3. 상세 내용

### 3.1 배경 / 목적
운영에 가까운 MariaDB 연동 스택을 한 번에 올리고, 무거운 ML 의존성으로 빌드가 멈추는 문제를 피한다.

### 3.2 변경 범위
- 추가: `backend/requirements.docker.txt`
- 수정: `Dockerfile`, `docker-compose.yml`, `app/db/__init__.py`

### 3.3 기술 포인트
- backend image slim (no torch)
- MariaDB healthcheck 후 backend start
- Docker Images UI는 전역 — 다른 프로젝트 이미지와 목록 혼재는 정상

### 3.4 의도적으로 하지 않은 것
- console 컨테이너 서비스 등록
- GPU 이미지

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] `docker compose -p cut_and_keep up -d`
- [x] `/health` → ok, db_dialect=mysql
- 결과: backend/frontend/mariadb/redis 기동 확인

### 4.2 부작용 / 리스크
- 호스트 6379 점유 시 Redis 매핑 변경 필요 (이미 6380)
- 3306 충돌 가능 (다른 MariaDB 스택)

### 4.3 후속 작업
- console 앱 추가
- docs 허브 폴더 구조

### 4.4 관련 문서
- `docs/Architecture/docker-topology.md`
- `docs/repeater/docker-redis-port.md`
