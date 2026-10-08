# Docker backend 의 호스트 포트를 BACKEND_PORT 로 바꿀 수 있게 / `6ce3eb92f9860904e12f2199ac2208ba3e88860d`

> 브랜치: `feature/media-quality`  
> 작성일: `2026-10-09 04:22`  
> 작성자: `agent`  
> 파일명: `261009_0422_6ce3eb9_docker-backend-port_feature-media-quality.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `chore(docker): Docker backend 의 호스트 포트를 BACKEND_PORT 로 바꿀 수 있게` |
| **커밋 번호 (SHA)** | `6ce3eb92f9860904e12f2199ac2208ba3e88860d` |
| **짧은 SHA** | `6ce3eb9` |
| **브랜치** | `feature/media-quality` |
| **부모 커밋** | `8e28af1` |

## 2. 주 커밋 내용

- `docker-compose.yml` backend 포트를 `${BIND_HOST}:${BACKEND_PORT:-8000}:8000` 으로

## 3. 상세 내용

### 3.1 배경 / 목적
검증 중 호스트에서 사용자가 띄운 `uvicorn --reload` 가 8000 을 쓰고 있어 Docker backend 가 포트를 못 잡아 뜨지 않았다.

### 3.2 변경 범위
- 수정: `docker-compose.yml`, `.env.example`

### 3.3 기술 포인트
- nginx 는 컨테이너 네트워크에서 `backend:8000` 으로 연결하므로 호스트 포트만 바꾸면 사용자 화면(:80)에 영향 없음

### 3.4 의도적으로 하지 않은 것
- 사용자 호스트 서버 중지

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] `BACKEND_PORT=8001` 로 Docker 기동, :80 실제 흐름 확인

### 4.2 부작용 / 리스크
- 없음 (기본값 8000 그대로)

### 4.3 후속 작업
- 없음

### 4.4 관련 문서
- `docs/guidance/security.md`
