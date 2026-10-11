# 서버가 내 PC 의 Ollama 를 SSH 터널로 연결해 쓰도록 / `45751aab541b6b2911a9b514e7434a4f76e336ec`

> 브랜치: `feature/pc-ollama-link`  
> 작성일: `2026-10-11 17:58`  
> 작성자: `agent`  
> 파일명: `261011_1758_45751aa_pc-ollama-link_feature-pc-ollama-link.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): 서버가 내 PC 의 Ollama 를 SSH 터널로 연결해 쓰도록` |
| **커밋 번호 (SHA)** | `45751aab541b6b2911a9b514e7434a4f76e336ec` |
| **짧은 SHA** | `45751aa` |
| **브랜치** | `feature/pc-ollama-link` |
| **부모 커밋** | `1322f77` |

## 2. 주 커밋 내용

- 서버(Oracle ARM)가 PC 의 Ollama 를 SSH 역방향 터널 + `ollama-bridge` 로 사용 — 모델을 서버에 받지 않음
- 서버 `.env`: `LLM_PROVIDER=ollama` · `LLM_FALLBACK=heuristic` · `DOCKER_LLM_BASE_URL=http://172.18.0.1:11434`
- Cloudflare 524 안내 문구

## 3. 상세 내용

### 3.1 배경 / 목적
서버가 `LLM_PROVIDER=heuristic` 이라 모델 선택 상자가 숨겨지고 해석이 키워드 파서로만 됐다. 사용자 지시: 모델을 새로 받지 말고 이미 있는 모델(PC)을 연결.
(처음에 서버 Ollama 컨테이너로 모델을 받다가 지시로 중단 · 컨테이너 · 파일 · 오버레이를 모두 삭제함)

### 3.2 변경 범위
- 추가: `docker-compose.pc-ollama.yml`, `scripts/ollama_tunnel.sh`, `docs/guidance/ollama-server.md`
- 수정: `frontend/src/api/client.ts`(524 안내) · 테스트, `docs/DEPLOYMENT.md`, `.env.example`
- 서버(저장소 밖): `.env` 3줄, iptables 규칙(172.18.0.0/16 → 11434, 저장), `docker-compose.pc-ollama.yml` 복사

### 3.3 기술 포인트
- 터널 끝은 서버 loopback(11435) — 외부 비노출. 다리는 docker 게이트웨이 주소에만 바인드
- 측정(서버 직접 주소): e4b 34s · 12b 57s · 27b 184s, 해석 parser=ollama 확인. Cloudflare 주소는 100초 제한(524)

### 3.4 의도적으로 하지 않은 것
- 서버에 모델 다운로드, 서버 CPU 로 모델 실행

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 공개 API `/llm/models` enabled · reachable · 3개 모델 available, 실제 사진 처리 3모델 성공 (직접 주소)
- [x] 프런트 vitest 85 · tsc · structure 테스트 통과

### 4.2 부작용 / 리스크
- PC 를 끄거나 터널이 끊기면 키워드 파서로 떨어짐 (서비스는 계속)
- 서버 작업 트리에 미추적 `docker-compose.pc-ollama.yml` — 다음 `git pull` 전에 삭제 필요

### 4.3 후속 작업
- 병합 지시 후: develop · main 병합, 서버 pull(미추적 파일 삭제 먼저), Cloudflare 프런트 재배포
