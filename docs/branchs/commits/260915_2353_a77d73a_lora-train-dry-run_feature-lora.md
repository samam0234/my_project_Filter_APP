# 피드백 기반 LoRA 학습 본선과 dry-run 추가 / `a77d73a5e2d73f7bb47274211352f37ec5b5676c`

> 브랜치: `feature/lora`  
> 작성일: `2026-09-15 23:53`  
> 작성자: `agent`  
> 파일명: `260915_2353_a77d73a_lora-train-dry-run_feature-lora.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 피드백 기반 LoRA 학습 본선과 dry-run 추가` |
| **커밋 번호 (SHA)** | `a77d73a5e2d73f7bb47274211352f37ec5b5676c` |
| **짧은 SHA** | `a77d73a` |
| **브랜치** | `feature/lora` |
| **부모 커밋** | `0473ff5051a0ee3bc3aa84dee3974bb8dfb0ffb1` |

## 2. 주 커밋 내용

- `training/lora/dataset.py` — 피드백/의사라벨 JSON → instruction 레코드
- `train_lora.py` — dry-run(peft 불필요) + 로컬 HF 체크포인트 PEFT 학습
- `scripts/fine_tune_lora.py` — 주간 배치 인자를 붙인 subprocess 래퍼
- 사용자 피드백 사이드카에 job `prompt` / `parsed_prompt` 보강
- 단위 테스트 `tests/unit/test_lora_dataset.py` (torch 없음)

## 3. 상세 내용

### 3.1 배경 / 목적

이전 LoRA 스캐폴드는 import 가드만 있고 학습 루프가 없었다.  
에이전트(바이브)가 데이터 계약·dry-run·PEFT 본선을 채우고,  
하드코딩 구간은 템플릿·vote 정책·주간 인자만 남긴다.

### 3.2 변경 범위

- 추가된 경로:
  - `training/lora/dataset.py`
  - `training/configs/lora.example.yaml`
  - `tests/unit/test_lora_dataset.py`
- 수정된 경로:
  - `training/lora/train_lora.py`, `training/lora/README.md`
  - `scripts/fine_tune_lora.py`, `scripts/README.md`
  - `backend/app/services/feedback_service.py`
  - `docs/plan/HARDCODING_ZONES.md`, `docs/plan/AI_MODEL_STRATEGY.md`
  - `models/README.md`, `training/README.md`, `training/requirements-training.txt`
  - `tests/structure/test_project_layout.py`, `tests/README.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트

- `--dry-run` 은 torch/peft 없이 동작. 실제 학습만 의존성 검사
- `--base-model` 은 로컬 HuggingFace 디렉터리만 (Ollama GGUF 불가, 허브 자동 다운 없음)
- dislike 는 시스템 parsed_prompt 를 정답으로 쓰지 않음. JSON 코멘트만 정답
- pipeline_failure 는 source 를 vote 보다 먼저 본다

### 3.4 의도적으로 하지 않은 것

- backend 프롬프트 분석기에 어댑터 핫스왑
- 비전(세그) LoRA — YOLO 본선은 `training/yolo/`
- develop / main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 로컬 실행 확인 (`--dry-run` exit 0, pytest structure + test_lora_dataset)
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: peft 없이 dry-run 과 단위 테스트 통과. 실제 어댑터 학습은 로컬 HF 체크포인트가 있을 때.

### 4.2 부작용 / 리스크

- 예전 피드백 JSON 에 prompt 가 없으면 레코드 0건
- 학습 시 `--base-model` 미지정이면 명확히 실패

### 4.3 후속 작업

- 세그 데이터 준비·학습 적용 스크립트는 별도 커밋
- (선택) `git push -u origin feature/lora`
- 완료 후 develop 병합 시 `git merge --no-ff`

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
- `training/lora/README.md`
- `docs/plan/LOGIC_STRUCTURE.md`
