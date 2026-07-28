# 학습 CUDA 환경과 실행 전 설정 가이드 추가 / `44ea564`

> 브랜치: `feature/yolo`  
> 작성일: `2026-07-28 16:50`  
> 작성자: `while`  
> 파일명: `260728_1650_44ea564_training-cuda-yolo-guide_feature-yolo.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(yolo): 학습 CUDA 환경과 실행 전 설정 가이드 추가` |
| **커밋 번호 (SHA)** | `44ea564afae264a35e31dc9033e3ffb5d6b0fd78` |
| **짧은 SHA** | `44ea564` |
| **브랜치** | `feature/yolo` |
| **부모 커밋** | develop 동기화 merge 이후 |

## 2. 주 커밋 내용

- `env_cuda.ps1` — 시스템 CUDA Toolkit(v13.3) PATH/CUDA_PATH 연결
- `setup_cuda_env.ps1` — training venv (원격 torch 휠 자동 설치 없음)
- `training/README.md` — 실행 전 names/keywords/마스크 필터 설정 + 실행 순서
- `requirements-training.txt` — torch 제외·시스템 CUDA 정책 명시
- `training/yolo/README.md` — 본 가이드 링크·빠른 실행

## 3. 상세 내용

### 3.1 배경 / 목적
학습 환경이 시스템 설치 CUDA 를 쓰도록 맞추고, 특정 개체 인식(클래스·프롬프트·필터) 설정을 문서화한다.

### 3.2 변경 범위
- 추가: `training/env_cuda.ps1`, `training/setup_cuda_env.ps1`
- 수정: `training/README.md`, `training/requirements-training.txt`, `training/yolo/README.md`

### 3.3 의도적으로 하지 않은 것
- pytorch.org 대용량 휠 자동 다운로드
- `.venv` / 가중치 커밋

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 스크립트·문서 반영
- 결과: torch 는 로컬 wheel 시 설치, 가이드에 명시

### 4.2 후속 작업
- `feature/yolo` → `develop` `--no-ff` 병합
- 로컬 torch wheel 경로 확보 후 학습 실행

### 4.3 관련 문서
- `training/README.md`
- `docs/branchs/TEMPLATE.md` (기록 위치: `docs/branchs/commits/`)
