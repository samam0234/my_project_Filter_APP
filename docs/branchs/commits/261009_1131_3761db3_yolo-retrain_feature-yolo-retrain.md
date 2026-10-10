# 세그 모델 재학습 루프 — 어려운 사례 수집 · 이어 학습 · 섞임/mAP 판정 · 배포 / `3761db3e2d05f089eb23f19163ee87a890d28b7a`

> 브랜치: `feature/yolo-retrain`  
> 작성일: `2026-10-09 11:31`  
> 작성자: `agent`  
> 파일명: `261009_1131_3761db3_yolo-retrain_feature-yolo-retrain.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(yolo): 세그 모델 재학습 루프 — 어려운 사례 수집 · 이어 학습 · 섞임/mAP 판정 · 배포` |
| **커밋 번호 (SHA)** | `3761db3e2d05f089eb23f19163ee87a890d28b7a` |
| **짧은 SHA** | `3761db3` |
| **브랜치** | `feature/yolo-retrain` |
| **부모 커밋** | `ba36381` |

## 2. 주 커밋 내용

- `scripts/retrain_yolo.py` 재학습 루프 (collect · train · eval · decide · deploy)
- 첫 실행 두 번(불채택) 결과 문서화

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "YOLO 재학습으로 오선택 · 섞임 개선". 후처리로 줄일 만큼 줄여 모델 쪽 경로를 준비.

### 3.2 변경 범위
- 추가: `scripts/retrain_yolo.py`, `tests/unit/test_retrain_yolo.py`, `docs/vaildates/yolo-retrain-20261009.md` · `yolo_retrain_20261009.json`
- 수정: learning-loop ⑥, FEATURES, scripts · training/yolo README, vaildates 색인

### 3.3 기술 포인트
- 판정: mAP 0.5%p 넘게 하락 금지 + 시나리오별 2%p 넘게 악화 금지 + 어려운 시나리오 2%p 넘게 개선 필요
- 공개 가중치가 COCO train2017 로 학습돼 같은 데이터 재학습은 효과 없음 → COCO 밖 사진 필요

### 3.4 의도적으로 하지 않은 것
- 불채택 모델 배포, 판정 기준 완화

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 테스트 432 통과
- [x] 루프 실제 실행 2회 (각 약 12~15분 학습 + 평가)

### 4.2 부작용 / 리스크
- 학습 중 스크립트 파일을 옮기면 Windows 작업자 프로세스가 실패 (문서화)

### 4.3 후속 작업
- HARD_EXAMPLE_CONF 수집 + 라벨링 후 --extra 로 재실행

### 4.4 관련 문서
- `docs/vaildates/yolo-retrain-20261009.md`
