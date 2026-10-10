# 서빙 세그 모델을 YOLO26m-seg 로 교체하고 재시도 신뢰도 버그 수정 / `2be3b358b8c8534519a0affaf5d2e00934562b8c`

> 브랜치: `feature/yolo-m`  
> 작성일: `2026-10-06 18:44`  
> 작성자: `agent`  
> 파일명: `261006_1844_2be3b35_yolo26m-default_feature-yolo-m.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(vision): 서빙 세그 모델을 YOLO26m-seg 로 교체하고 재시도 신뢰도 버그 수정` |
| **커밋 번호 (SHA)** | `2be3b358b8c8534519a0affaf5d2e00934562b8c` |
| **짧은 SHA** | `2be3b35` |
| **브랜치** | `feature/yolo-m` |
| **부모 커밋** | `302e2d7` (feature/retrain-loop) |

## 2. 주 커밋 내용

- 서빙 기본 세그 모델: 직접 학습 5클래스 YOLO26s-seg → COCO YOLO26m-seg (80클래스)
- 재시도 시 낮춘 신뢰도가 실제로 적용되도록 `predict(conf=)` 전달
- 공정 비교 실험 스크립트와 전환 문서

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 "다음 할 일" 5번 — 사람 검출률 개선. 사용자가 m 교체를 승인 (규칙상 기본 s 였음).

### 3.2 변경 범위

- 추가: `scripts/experiments/seg_model_compare.py`, `docs/plan/YOLO26M_DEFAULT.md`
- 수정: `backend/app/{core/config.py, services/segmentation.py}`, `tests/unit/{test_config,test_segmentation_filter}.py`,
  규칙 파일(`AGENTS.md`, `.agents`·`.grok` 스킬, `.grok/rules`), 안내 문서 15곳, `frontend` 홈·하단 문구,
  `.env.example`, `scripts/convert_to_onnx.py`
- 저장소 밖: `backend/models/yolo26m-seg.pt`, `models/yolo26m-seg.pt` (git 무시), 로컬 `.env` 의 `YOLO_MODEL_PATH` (s 는 주석으로 남김)

### 3.3 기술 포인트

- 서빙 중이던 s 가 COCO 원본이 아니라 **직접 학습한 5클래스** 임을 확인 → 버스·의자 등은 해석이 맞아도 결과가 비었다
- 첫 비교셋(cutnkeep_seg_5k val)이 COCO train2017 출신 → COCO 사전학습 m 이 본 사진이라 부풀려짐(91.9%) → COCO val2017 로 재측정
- 입력 크기 확대·신뢰도 하향은 오히려 나빠짐 (모델이 640 학습)
- 가짜 YOLO 테스트가 Ultralytics 처럼 conf 미만을 거르도록 바꿔, 신뢰도 미전달 버그를 테스트가 잡게 함

### 3.4 의도적으로 하지 않은 것

- l 모델 (m 대비 +1%p 수준, 더 무거움)
- 학습 스크립트 기본 가중치·`apply_best.py` 변경 (직접 학습 흐름은 별개)
- 세그 모델 재학습 (직접 학습본이 COCO 원본보다 낮아 출발점부터 재검토 필요)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 모델 (COCO val2017 600장) | 검출률 | 오검출 | 선택 정확도 |
|---------------------------|--------|--------|-------------|
| s 직접 학습 (이전) | 81.1% | 343 | 74.3% |
| s COCO | 86.3% | 306 | 78.2% |
| **m COCO (현재)** | **88.0%** | **301** | **79.5%** |

- 실제 서빙: 로컬 GPU · Docker CPU 모두 m 로드 확인, Docker CPU 세그 225~345 ms
- [x] pytest 전체 통과 (신뢰도 전달 검증 추가), frontend vitest 16 · 빌드 성공

### 4.2 부작용 / 리스크

- 세그 시간 약 2배 (요청 전체 대비 작음), 가중치 52 MB
- 기존 `.env` 를 쓰는 다른 PC 는 `YOLO_MODEL_PATH` 를 직접 바꾸고 m 가중치를 배치해야 함

### 4.3 후속 작업

- 세그 재학습은 COCO 원본에서 출발, `seg_model_compare.py` 로 비교

### 4.4 관련 문서

- `docs/plan/YOLO26M_DEFAULT.md`
