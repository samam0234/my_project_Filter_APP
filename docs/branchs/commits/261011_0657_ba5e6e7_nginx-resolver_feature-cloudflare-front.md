# backend 가 다시 만들어져도 502 가 나지 않게 주소를 다시 찾음 / `ba5e6e7f5448ac809605c9b898c99f72c35fe045`

> 브랜치: `feature/cloudflare-front`  
> 작성일: `2026-10-11 06:57`  
> 작성자: `agent`  
> 파일명: `261011_0657_ba5e6e7_nginx-resolver_feature-cloudflare-front.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(nginx): backend 가 다시 만들어져도 502 가 나지 않게 주소를 다시 찾음` |
| **커밋 번호 (SHA)** | `ba5e6e7f5448ac809605c9b898c99f72c35fe045` |
| **짧은 SHA** | `ba5e6e7` |
| **브랜치** | `feature/cloudflare-front` |
| **부모 커밋** | `55b1422` |

## 2. 주 커밋 내용

- `frontend/nginx.conf`: `resolver 127.0.0.11 valid=10s` + `proxy_pass http://$backend_upstream` — backend IP 가 바뀌어도 따라감
- `docs/guidance/cloudflare-deploy.md`: 502 진단 순서와 실제 사례

## 3. 상세 내용

### 3.1 배경 / 목적
Cloudflare 화면에서 "서버 연결 안 됨". 원인은 Worker 가 아니라 서버: `EDGE_SECRET` 을 `.env` 에 넣자 backend 가 재생성되어 IP 가 바뀌었고, nginx 가 옛 IP(172.18.0.7)로 접속해 connection refused → 502.

### 3.2 변경 범위
- 수정: `frontend/nginx.conf`, `docs/guidance/cloudflare-deploy.md`

### 3.3 기술 포인트
- 변수로 proxy_pass 하면 URI 를 붙이지 않아 요청 경로(/api/... · /health)가 그대로 전달 — 기존 매핑과 동일
- 서버: 실행 중 컨테이너에서 `nginx -t` 통과 확인 후 적용, frontend 이미지 재빌드로 고정 (백업 `~/nginx.conf.bak`)

### 3.4 의도적으로 하지 않은 것
- 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] backend 강제 재생성 후 10초 안에 Worker `/health` 200 (자동 복구)
- [x] Worker 경유 가입 201 · 세션 유지 · 로그아웃 401 · 재로그인 200, 서버 로그에 실제 사용자 IP — 테스트 계정 삭제 완료

### 4.2 부작용 / 리스크
- 서버 작업 트리 `frontend/nginx.conf` 도 직접 반영됨 → 다음 `git pull` 전 `git checkout -- frontend/nginx.conf` 필요

### 4.3 후속 작업
- develop · main 병합 · 푸시 후 서버를 git 기준으로 맞추기
