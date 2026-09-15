# COCO 5k 세그 데이터 준비 스크립트 추가 / `f7685c1341b0fcd7b230da442cdc474b407f24f2`

> 브랜치: `feature/lora`  
> 작성일: `2026-09-16 02:09`  
> 작성자: `agent`  
> 파일명: `260916_0209_f7685c1_coco5k-seg-prepare_feature-lora.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(yolo): COCO 5k 세그 데이터 준비 스크립트 추가` |
| **커밋 번호 (SHA)** | `f7685c1341b0fcd7b230da442cdc474b407f24f2` |
| **짧은 SHA** | `f7685c1` |
| **브랜치** | `feature/lora` |
| **부모 커밋** | `d690b9a5aac605b5ead79fe14d8551d0ecc484b4` |

## 2. 주 커밋 내용

- `prepare_coco5k_seg.py` — COCO train2017 에서 5클래스 ~5000장 샘플·다운로드·YOLO-seg 변환
- 같은 이미지 라벨로 `data/pseudo_labels` LoRA JSON 생성
- `dataset_seg.yaml` path 를 `cutnkeep_seg_5k` 로 변경
- `training/models/` gitignore (Qwen 등 HF 베이스 체크포인트)

## 3. 상세 내용

### 3.1 배경 / 목적

coco128 77장 스모크 다음으로, 학습에 쓸 만한 규모(약 5k)의 공식 폴리곤 셋이 필요했다.  
train2017 zip(18GB) 대신 어노테이션 + 대상 JPEG 만 받는다.

### 3.2 변경 범위

- 추가된 경로: `training/yolo/prepare_coco5k_seg.py`
- 수정된 경로: `training/configs/dataset_seg.yaml`, `training/yolo/README.md`, `.gitignore`
- 삭제된 경로: 없음

### 3.3 기술 포인트

- category **name** 으로 매핑 (COCO id 구멍과 Ultralytics 0-index 혼동 방지)
- iscrowd·작은 인스턴스 제외, dog/cat/bag/car 쿼터 후 person 으로 5000 채움
- yaml `path` 는 상대 경로 유지 (`train_segment.py` 가 학습 직전 절대 경로화)

### 3.4 의도적으로 하지 않은 것

- 5000장 JPEG·`best.pt`·LoRA adapter·Qwen 가중치 커밋
- develop / main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 로컬 실행 확인 (5000장 다운로드 실패 0, YOLO 40 epoch, LoRA 3 epoch)
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 스크립트와 yaml·gitignore 만 커밋. 산출 가중치는 `models/` 로컬 적용 상태.

### 4.2 부작용 / 리스크

- `dataset_seg.yaml` 이 5k 경로를 가리키므로 coco128 소량셋으로 되돌리려면 yaml 을 다시 써야 함
- 네트워크 없이 `prepare_coco5k_seg.py` 재실행은 캐시된 `coco_raw` 가 있을 때만 가능

### 4.3 후속 작업

- (선택) `git push origin feature/lora`
- 완료 후 develop 병합 시 `git merge --no-ff`

### 4.4 관련 문서

- `training/yolo/README.md`
- `training/lora/README.md`
