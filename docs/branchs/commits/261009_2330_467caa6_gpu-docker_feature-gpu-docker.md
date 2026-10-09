# GPU 서버(CUDA)로 띄우는 오버레이 — 문장 해석 LoRA · 세그 GPU, 점검 · 모델 묶음 --gpu / `467caa6ed96ff4e9db52c99a07b12f59f1eb5f10`

> 브랜치: `feature/gpu-docker`  
> 작성일: `2026-10-09 23:30`  
> 작성자: `agent`  
> 파일명: `261009_2330_467caa6_gpu-docker_feature-gpu-docker.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): GPU 서버(CUDA)로 띄우는 오버레이 — 문장 해석 LoRA · 세그 GPU, 점검 · 모델 묶음 --gpu` |
| **커밋 번호 (SHA)** | `467caa6ed96ff4e9db52c99a07b12f59f1eb5f10` |
| **짧은 SHA** | `467caa6` |
| **브랜치** | `feature/gpu-docker` |
| **부모 커밋** | `d5436e8` |

## 2. 주 커밋 내용

- `docker-compose.gpu.yml` · Dockerfile `TORCH_INDEX`
- 점검 · 모델 묶음 `--gpu`, GPU 배포 안내

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시 "GPU 서버로 CUDA 실행 할 수 있도록" + "점검 ㄱㄱ".

### 3.2 변경 범위
- 추가: `docker-compose.gpu.yml`, `docs/guidance/gpu-deploy.md`
- 수정: `backend/Dockerfile`, `scripts/deploy_check.py`, `scripts/models_bundle.py`, `tests/unit/test_deploy_tools.py`, https-deploy · llm-and-vision · FEATURES · .env.example · guidance README

### 3.3 기술 포인트
- GPU 이미지는 이름을 따로(cut_and_keep-backend-gpu) 두어 CPU 이미지와 섞이지 않게
- 폴백을 키워드 파서로 — Ollama 를 같은 GPU 에 또 올리면 12GB 카드에서 넘침
- 시험 중 해석 이상은 Git Bash curl 의 한글 깨짐이었음 (서비스 문제 아님, 문서화)

### 3.4 의도적으로 하지 않은 것
- onnxruntime GPU (SegFormer · LaMa) — cuDNN 맞추기 부담, 지금은 CPU 로 충분

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 컨테이너 CUDA · LoRA 1.85초/문장 · HTTPS 처리 5건 정답
- [x] 전체 테스트 448 통과, 로컬 Docker 일반 모드로 복원

### 4.2 부작용 / 리스크
- GPU 이미지 13GB (디스크)
- 첫 요청은 모델 로드로 느림 (해석 30초 넘으면 키워드 파서)

### 4.3 후속 작업
- 실서버에서 deploy_check remote · server --gpu

### 4.4 관련 문서
- `docs/guidance/gpu-deploy.md`
