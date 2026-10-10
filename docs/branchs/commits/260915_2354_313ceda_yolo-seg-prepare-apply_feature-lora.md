# 5클래스 세그 데이터 준비와 학습 적용 스크립트 추가 / `313ceda4303d40d7468d2159b5bdc05022f66d0e`

> 브랜치: `feature/lora`  
> 작성일: `2026-09-15 23:54`  
> 작성자: `agent`  
> 파일명: `260915_2354_313ceda_yolo-seg-prepare-apply_feature-lora.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(yolo): 5클래스 세그 데이터 준비와 학습 적용 스크립트 추가` |
| **커밋 번호 (SHA)** | `313ceda4303d40d7468d2159b5bdc05022f66d0e` |
| **짧은 SHA** | `313ceda` |
| **브랜치** | `feature/lora` |
| **부모 커밋** | `e1f178fa6fe329f1abf352996cbdf26591778ed6` |

## 2. 주 커밋 내용

- `prepare_cutnkeep_seg.py` — coco128-seg → person/dog/cat/car/bag 폴리곤 셋
- `train_segment.py` — yaml 상대 `path` 를 학습 직전에 절대 경로로 해석, `--workers`
- `apply_best.py` — `best.pt` → `models/yolo26s-seg.pt` + 샘플 세그 추론
- `configs/dataset_seg.yaml` — 5클래스 계약 (상대 경로, 머신 절대 경로 없음)
- 로컬 서빙 `ultralytics>=8.4.0` (YOLO26 가중치)

## 3. 상세 내용

### 3.1 배경 / 목적

세그 학습 데이터가 비어 있고 yaml 상대 경로가 Ultralytics `datasets_dir` 에 먹혀 실패했다.  
변환 스크립트와 경로 해석을 넣어 같은 5클래스 파이프라인을 재현 가능하게 한다.

### 3.2 변경 범위

- 추가된 경로:
  - `training/yolo/prepare_cutnkeep_seg.py`
  - `training/yolo/apply_best.py`
  - `training/configs/dataset_seg.yaml`
- 수정된 경로:
  - `training/yolo/train_segment.py`, `training/yolo/README.md`
  - `requirements.txt`, `.gitignore` (`*.resolved.yaml`)
- 삭제된 경로: 없음

### 3.3 기술 포인트

- bag = COCO backpack + handbag + suitcase
- 학습 산출물(`.pt`, `datasets/`, `outputs/`) 은 gitignore 유지
- `dataset_seg.yaml` 의 path 는 `../datasets/cutnkeep_seg` (yaml 기준)

### 3.4 의도적으로 하지 않은 것

- 대용량 데이터셋·가중치 커밋
- develop / main 병합
- Docker 이미지에 torch 추가

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 로컬 실행 확인 (coco128 변환 77장, 20 epoch 학습, apply_best 마스크 추론)
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: `models/yolo26s-seg.pt` 배치 후 val 이미지에서 person/dog 마스크 확인. 가중치는 커밋하지 않음.

### 4.2 부작용 / 리스크

- val 15장·사람 편중. bag/car 샘플이 적어 해당 클래스 품질은 참고 수준
- 백엔드에서 YOLO26 를 쓰려면 ultralytics 8.4+ 와 학습 venv/로컬 설치가 필요

### 4.3 후속 작업

- backend 재시작 후 업로드 e2e
- (선택) `git push origin feature/lora`
- 완료 후 develop 병합 시 `git merge --no-ff`

### 4.4 관련 문서

- `training/yolo/README.md`
- `training/README.md`
- `docs/plan/YOLO26S_DEFAULT.md`
