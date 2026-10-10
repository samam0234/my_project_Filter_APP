# GPU 오버레이에서 CUDA 판 고르기(GPU_TORCH_INDEX) — cu128 기본 · cu130 실측 / `49fd9224179a7c17b143b0d5d55962c8fdb0bb2d`

> 브랜치: `feature/cuda-option`  
> 작성일: `2026-10-10 05:31`  
> 작성자: `agent`  
> 파일명: `261010_0531_49fd922_cuda-option_feature-cuda-option.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): GPU 오버레이에서 CUDA 판 고르기(GPU_TORCH_INDEX) — cu128 기본 · cu130 실측` |
| **커밋 번호 (SHA)** | `49fd9224179a7c17b143b0d5d55962c8fdb0bb2d` |
| **짧은 SHA** | `49fd922` |
| **브랜치** | `feature/cuda-option` |
| **부모 커밋** | `14b6982` |

## 2. 주 커밋 내용

- GPU 오버레이 `GPU_TORCH_INDEX` (cu128 기본 · cu130)
- CUDA 판 실측과 안내

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 질문 "CUDA 13.3 설치돼 있는데 왜 12.8" — 판을 고를 수 있게 하고 실측으로 결정 근거를 남김.

### 3.2 변경 범위
- 수정: `docker-compose.gpu.yml`, `.env.example`, `scripts/deploy_check.py`, `docs/guidance/gpu-deploy.md`

### 3.3 기술 포인트
- 컨테이너는 휠 안의 CUDA 런타임 + 호스트 드라이버만 씀 → 호스트 Toolkit 버전은 무관
- 속도 측정이 시스템 상태에 흔들려 순서를 바꿔 재측정 — 차이 없음으로 결론

### 3.4 의도적으로 하지 않은 것
- 기본을 cu130 으로 (드라이버 580 미만 서버에서 안 돎)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] cu130 이미지 GPU 인식 · LoRA 정상, 전체 테스트 통과

### 4.2 부작용 / 리스크
- 없음 (기본값 그대로)

### 4.3 후속 작업
- 실서버 드라이버 확인 후 판 결정

### 4.4 관련 문서
- `docs/guidance/gpu-deploy.md`
