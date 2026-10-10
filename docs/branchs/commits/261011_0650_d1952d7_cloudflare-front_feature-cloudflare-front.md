# 프런트엔드를 Cloudflare Worker 로 배포 — 정적 화면 + /api 프록시 / `d1952d7edc6faa10bf4488f344f102fad9c37394`

> 브랜치: `feature/cloudflare-front`  
> 작성일: `2026-10-11 06:50`  
> 작성자: `agent`  
> 파일명: `261011_0650_d1952d7_cloudflare-front_feature-cloudflare-front.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(cloudflare): 프런트엔드를 Cloudflare Worker 로 배포 — 정적 화면 + /api 프록시` |
| **커밋 번호 (SHA)** | `d1952d7edc6faa10bf4488f344f102fad9c37394` |
| **짧은 SHA** | `d1952d7` |
| **브랜치** | `feature/cloudflare-front` |
| **부모 커밋** | `25b3144` |

## 2. 주 커밋 내용

- Cloudflare Worker `cutnkeep-front` 로 프런트엔드 배포 (정적 화면 + `/api/*` · `/health` 프록시)
- Caddy: 비밀 값(EDGE_SECRET)이 맞는 요청만 `X-Cnk-Real-IP` 를 실제 사용자 IP 로 사용
- 정적 파일 보안 헤더 `_headers`, 비밀 값 저장 스크립트 `set_edge_secret.sh`, 문서

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시("프론트엔드만 배포")로 화면을 Cloudflare 에 올림. 화면과 API 를 같은 주소로 보이게 해 로그인 쿠키(SameSite=Lax)가 그대로 동작하게 한다.

### 3.2 변경 범위
- 추가: `deploy/cloudflare/*`, `frontend/public/_headers`, `docs/guidance/cloudflare-deploy.md`
- 수정: `docker/caddy/Caddyfile`, `docker-compose.https.yml`, `docs/DEPLOYMENT.md`, `.env.example`, `.gitignore`

### 3.3 기술 포인트
- Worker 가 사용자 IP 를 전달하지 않으면 서버 속도 제한이 Cloudflare IP 하나로 묶임 → 비밀 값 일치 시에만 신뢰
- 서버 Caddyfile · compose 를 서버에 직접 반영(백업 `~/Caddyfile.bak`), 서버 작업 트리가 repo 와 달라 다음 `git pull` 전 `git checkout -- docker/caddy docker-compose.https.yml` 필요

### 3.4 의도적으로 하지 않은 것
- 운영 콘솔 배포 (사용자 지시: 프런트엔드만, 접근 제한 필요)
- EDGE_SECRET 저장 (비밀 값 저장은 사용자가 스크립트로 직접)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] Worker 배포, 화면 · SPA 경로 200, 보안 헤더 확인
- [ ] `/api` 는 EDGE_SECRET 설정 전이라 500 — 스크립트 실행 뒤 가입 · 로그인 · 업로드 확인 필요

### 4.2 부작용 / 리스크
- 영상 · GIF · 큰 모델의 오래 걸리는 요청이 Worker 를 거쳐 끊길 수 있음 (실측 필요)

### 4.3 후속 작업
- `set_edge_secret.sh` 실행 → 실제 로그인 · 처리 확인 → main 병합 · 푸시
