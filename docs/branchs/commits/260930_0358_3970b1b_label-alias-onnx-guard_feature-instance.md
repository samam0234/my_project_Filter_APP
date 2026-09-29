# 라벨 별칭과 ONNX 세션 가드 추가 / `3970b1b9d6ecdf292af2ba0831bf06cf2035e113`

> 브랜치: `feature/instance`  
> 작성일: `2026-09-30 03:58`  
> 작성자: `agent`  
> 파일명: `260930_0358_3970b1b_label-alias-onnx-guard_feature-instance.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(yolo): 라벨 별칭과 ONNX 세션 가드 추가` |
| **커밋 번호 (SHA)** | `3970b1b9d6ecdf292af2ba0831bf06cf2035e113` |
| **짧은 SHA** | `3970b1b` |
| **브랜치** | `feature/instance` |
| **부모 커밋** | `db66946` |

## 2. 주 커밋 내용

- `segmentation.expand_targets`: 요청 라벨 ↔ 서빙 모델 라벨 양방향 별칭 (`bag` ↔ `handbag`·`backpack`·`suitcase` 등)
- `onnx_utils.create_session`: `.onnx` 파일에만 세션 생성, 로드 실패도 `None` → stub 폴백
- 단위 테스트 2개

## 3. 상세 내용

### 3.1 배경 / 목적

1. 서빙 중인 5클래스 모델은 가방을 `bag` 으로, LLM·LoRA 는 COCO `handbag`·`backpack` 으로 부른다.
   "가방만 남겨"가 대상 없음(failed)으로 끝났다.
2. LoRA 학습 중 시스템 메모리가 부족해 백엔드의 torch 로드가 `WinError 1455` 로 실패했을 때,
   Segmentor 가 `.pt` 를 onnxruntime 으로 열다가 `INVALID_PROTOBUF` 예외 → 업로드 요청 자체가 failed.
   설계상 모델을 못 쓰면 stub 으로 넘어가야 한다.

### 3.2 변경 범위

- 수정된 경로: `backend/app/services/segmentation.py`, `backend/app/utils/onnx_utils.py`,
  `tests/unit/test_segmentation_filter.py`

### 3.3 기술 포인트

- 별칭은 canonical ↔ 별칭 양방향이라 모델이 어느 쪽 이름을 쓰든 동작
- ONNX 분기(`_predict_onnx`)는 여전히 하드코딩 구간 — 여기서는 잘못된 파일로 멈추지 않게만 함

### 3.4 의도적으로 하지 않은 것

- 서빙 모델을 COCO 80 클래스로 교체 (별도 결정 필요)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 통과
- [x] 실제 서버: 메모리 회복 후 `--reload` 재기동, 업로드 API 정상

### 4.2 부작용 / 리스크

- 없음

### 4.3 후속 작업

- ONNX predict 구현, 서빙 모델 어휘 결정

### 4.4 관련 문서

- `backend/models/README.md`
