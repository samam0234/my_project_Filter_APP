# 백엔드 이미지에 LoRA 해석 패키지를 넣는 선택형 빌드(LLM_LORA=1), CPU 실측 기록 / `2748ed1af77af9f4895d1a5fcb57ca14ea8521e9`

> 브랜치: `feature/docker-lora`  
> 작성일: `2026-10-09 20:54`  
> 작성자: `agent`  
> 파일명: `261009_2054_2748ed1_docker-lora_feature-docker-lora.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(docker): 백엔드 이미지에 LoRA 해석 패키지를 넣는 선택형 빌드(LLM_LORA=1), CPU 실측 기록` |
| **커밋 번호 (SHA)** | `2748ed1af77af9f4895d1a5fcb57ca14ea8521e9` |
| **짧은 SHA** | `2748ed1` |
| **브랜치** | `feature/docker-lora` |
| **부모 커밋** | `98fad0e` |

## 2. 주 커밋 내용

- 백엔드 Dockerfile `LLM_LORA` 빌드 인자, compose · .env.example
- CPU 컨테이너 실측과 문서

## 3. 상세 내용

### 3.1 배경 / 목적
해석 비교에서 "Docker 이미지에 transformers 가 없어 혼합 방식을 못 씀" 이 남은 일이었다.

### 3.2 변경 범위
- 수정: `backend/Dockerfile`, `docker-compose.yml`, `.env.example`, `docs/guidance/llm-and-vision.md`, `docs/vaildates/parser-compare-20261009.md`

### 3.3 기술 포인트
- 실제로 이미지를 빌드해 컨테이너에서 측정 — CPU 로는 문장당 평균 23초라 실사용 불가로 결론

### 3.4 의도적으로 하지 않은 것
- GPU(CUDA) 이미지 — NVIDIA 컨테이너 런타임 · 이미지 크기 부담, 실서버 GPU 여부 미정

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] LLM_LORA=1 이미지 빌드 · LoRA 해석 동작 확인, 전체 테스트 통과

### 4.2 부작용 / 리스크
- 없음 (기본 0)

### 4.3 후속 작업
- GPU 서버면 CUDA 이미지 검토

### 4.4 관련 문서
- `docs/guidance/llm-and-vision.md`
