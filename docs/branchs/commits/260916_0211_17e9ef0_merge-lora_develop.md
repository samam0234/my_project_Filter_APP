# feature/lora → develop 병합 (no-ff) / `17e9ef08ecca6cd6aa91fcb2ba671912c024a517`

> 브랜치: `develop`  
> 작성일: `2026-09-16 02:11`  
> 작성자: `agent`  
> 파일명: `260916_0211_17e9ef0_merge-lora_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/lora into develop (no-ff)` |
| **커밋 번호 (SHA)** | `17e9ef08ecca6cd6aa91fcb2ba671912c024a517` |
| **짧은 SHA** | `17e9ef0` |
| **브랜치** | `develop` |
| **부모 커밋** | `0473ff5` (develop), `f4b80e9` (feature tip) |

## 2. 주 커밋 내용

- `feature/lora` 를 develop 에 **no-ff** 병합
- LoRA 학습 본선·dry-run (`a77d73a`)
- 5클래스 세그 파이프라인 (`313ceda`)
- COCO 5k 준비 스크립트 (`f7685c1`)

## 3. 상세 내용

### 3.1 배경 / 목적

피드백 LoRA 본선과 YOLO-seg 5클래스/5k 데이터 파이프라인을  
통합 브랜치 develop 에 반영한다.

### 3.2 변경 범위

- `training/lora/` (`dataset.py`, `train_lora.py`, README)
- `training/yolo/` (`prepare_cutnkeep_seg.py`, `prepare_coco5k_seg.py`, `apply_best.py`, `train_segment.py`)
- `scripts/fine_tune_lora.py`, `backend/app/services/feedback_service.py`
- `tests/unit/test_lora_dataset.py`
- branchs 커밋 기록 3건

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 학습 산출(`.pt`, 5k JPEG, Qwen 가중치, adapter) 은 gitignore 유지

### 3.4 의도적으로 하지 않은 것

- main 병합 (배포 라인, release 경유)
- 원격 푸시 (로컬 병합만)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 로컬 develop 이 origin/develop 보다 7 커밋 앞섬 (병합 커밋 + feature 6)
- 그래프에 merge bubble 유지

### 4.2 부작용 / 리스크

- `dataset_seg.yaml` 기본 path 가 `cutnkeep_seg_5k` — 데이터 없으면 train 전 `prepare_coco5k_seg.py` 필요
- YOLO26 서빙은 ultralytics 8.4+ 필요

### 4.3 후속 작업

- (선택) `git push origin develop`
- (선택) `git push origin feature/lora`
- main 은 release 경유 후 `--no-ff`

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
- `docs/branchs/commits/260915_2353_a77d73a_lora-train-dry-run_feature-lora.md`
- `docs/branchs/commits/260915_2354_313ceda_yolo-seg-prepare-apply_feature-lora.md`
- `docs/branchs/commits/260916_0209_f7685c1_coco5k-seg-prepare_feature-lora.md`
