# feature/gpu-docker → develop 병합 (no-ff) / `97071c7a943ce1e73805e0869aa5a5597059364f`

> 브랜치: `develop`
> 작성일: `2026-10-10 05:33`
> 작성자: `agent`
> 파일명: `261010_0533_97071c7_merge-gpu-docker_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/gpu-docker into develop (no-ff)` |
| **커밋 번호 (SHA)** | `97071c7a943ce1e73805e0869aa5a5597059364f` |
| **짧은 SHA** | `97071c7` |
| **브랜치** | `develop` |
| **부모 커밋** | `d5436e8` (develop), `a8364f1` (feature/gpu-docker 끝) |

## 2. 주 커밋 내용

GPU 서버(CUDA) 오버레이 — 문장 해석 LoRA · 세그 GPU, 점검 · 모델 묶음 --gpu, 로컬 리허설(LoRA 1.85초/문장)

병합된 커밋:
- `a8364f1` docs(branchs): 커밋 기록 467caa6 추가
- `467caa6` feat(deploy): GPU 서버(CUDA)로 띄우는 오버레이 — 문장 해석 LoRA · 세그 GPU, 점검 · 모델 묶음 --gpu

## 3. 상세 내용

### 3.1 배경 / 목적
"아직 부족한 부분" 중 병합을 맨 마지막으로 하라는 지시(2026-10-10)에 따라, GPU 오버레이 · 실제 영상 검증 · 운영 env · CUDA 판 작업을 각 브랜치에 모두 커밋한 뒤 **한 번에 총 병합** (병합 시점 규칙).

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음 (병합 결과 트리 = feature/cuda-option)
- 쌓인 순서대로: gpu-docker → davis-eval → prod-env → cuda-option

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 백엔드 pytest 451 · 프론트 vitest 54 통과

### 4.2 부작용 / 리스크
- GPU 이미지 13GB(cu128) — 디스크
- DAVIS 데이터(약 800MB)는 git 밖 training/datasets/davis

### 4.3 후속 작업
- 실서버: make_prod_env → GPU/HTTPS 오버레이로 띄우기 → deploy_check remote · server --gpu, 서버 드라이버에 맞춰 GPU_TORCH_INDEX 결정

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
