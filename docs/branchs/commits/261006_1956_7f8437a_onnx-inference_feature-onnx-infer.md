# ONNX 세그 추론 직접 구현과 슬림 Docker 이미지 / `7f8437afc8fc5da77f5900c0244799df02eff724`

> 브랜치: `feature/onnx-infer`  
> 작성일: `2026-10-06 19:56`  
> 작성자: `agent`  
> 파일명: `261006_1956_7f8437a_onnx-inference_feature-onnx-infer.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(vision): ONNX 세그 추론 직접 구현과 슬림 Docker 이미지` |
| **커밋 번호 (SHA)** | `7f8437afc8fc5da77f5900c0244799df02eff724` |
| **짧은 SHA** | `7f8437a` |
| **브랜치** | `feature/onnx-infer` |
| **부모 커밋** | `6edd18b` (develop) |

## 2. 주 커밋 내용

- `onnx_utils` 전·후처리와 `Segmentor._predict_onnx` — onnxruntime 만으로 세그
- Docker 빌드 인자 `SEG_RUNTIME=onnx` — 이미지 2.81 → 1.11 GB
- `.pt` 경로도 `retina_masks=True` 로 경계 정확도 개선

## 3. 상세 내용

### 3.1 배경 / 목적

남은 항목 중 "ONNX 추론"(코드에 직접 구현 대상 `[하드코딩 파트]` 로 비워 둔 구간). 사용자가 배포 제외 나머지를 진행하라고 해서 구현.
앞서 사용자가 Docker 에서 "ultralytics 설치" 를 택해 ONNX 는 안 건드렸었다 — 이번에 채워 두 경로를 모두 제공.

### 3.2 변경 범위

- 추가: `tests/unit/test_onnx_inference.py`, `scripts/experiments/onnx_vs_pt.py`, `docs/plan/ONNX_INFERENCE.md`
- 수정: `backend/app/{utils/onnx_utils.py, services/segmentation.py, core/config.py}`, `backend/Dockerfile`, `docker-compose.yml`,
  `.env.example`, `tests/unit/test_segmentation_filter.py`, `docs/{plan/HARDCODING_ZONES.md, guidance/docker-run.md}`, `models/README.md`, `scripts/README.md`
- 저장소 밖: `backend/models/yolo26m-seg.onnx`, `models/yolo26m-seg.onnx` (git 무시)

### 3.3 기술 포인트

- 출력 `[1,116,8400]` 은 NMS 없는 전통 형식 → 클래스별 NMS 를 cv2.dnn.NMSBoxes 로 직접
- 처음엔 박스 자르기를 160 격자에서 먼저 해서 Ultralytics 와 IoU 0.89 → 원본 해상도에서 자르는 정밀 방식으로 0.973
- 비교 기준을 두 번 틀림: `masks.data` 단순 확대(패딩 어긋남), `masks.xy` 폴리곤(가장 큰 윤곽만) → `retina_masks=True` 가 맞는 기준
- 그 과정에서 **백엔드 `.pt` 경로의 단순 확대 마스크가 부정확**함을 발견 (정답 대비 0.825) → 같은 브랜치에서 수정
- 재시도 낮춘 신뢰도는 ONNX 에서 출력 필터로 바로 적용 (`conf=` 인자 없음)

### 3.4 의도적으로 하지 않은 것

- GPU onnxruntime (배포 서버 사양 결정 후)
- 동적 입력 크기 export (640 고정)
- 속도 최적화 (마스크 복원이 인스턴스마다 원본 해상도 연산 — 로컬 PC 에서 장당 약 1.1 s, Docker 는 250~310 ms)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 항목 | 결과 |
|------|------|
| 내 구현 vs Ultralytics 가 같은 ONNX 를 돌린 결과 | 마스크 IoU 평균 0.973 · 중앙 1.000 (100장) |
| `.pt` vs ONNX (200장) | 검출률 88.8% / 89.3%, 위치 선택 81.1% / 81.5%, 마스크 IoU 평균 0.928 |
| 정답 폴리곤 대비 경계 IoU | `.pt` 단순 확대(이전) 0.825 → `.pt` 정밀 0.848 · ONNX 0.848 |
| Docker 이미지 | 2.81 GB → **1.11 GB** (슬림 컨테이너에 ultralytics·torch 없음, 요청 6건 정상) |

- [x] pytest 전체 통과 (신규 11건: 합성 출력으로 letterbox·NMS·패딩 제거·재시도 기준·라벨 필터)

### 4.2 부작용 / 리스크

- **사고:** 검증 중 Ultralytics 가 `onnxruntime-gpu` 를 자동 설치해 학습 venv 의 onnxruntime 이 깨짐 →
  `pip install --force-reinstall --no-deps onnxruntime==1.19.2` 로 복구 (1.19.2, CPU 정상 확인). 같은 venv 에 `onnx 1.23.2` 가 새로 설치됨 (export 용)
- 이후 실험은 `YOLO_AUTOINSTALL=False`. 백엔드는 `.onnx` 를 ultralytics 로 열지 않음
- 학습 venv 의 ultralytics 가 8.4.152 로 올라 있음 (Dockerfile 고정 버전과 같음)

### 4.3 후속 작업

- 배포 서버에서 ONNX vs ultralytics CPU 속도 재측정 후 이미지 선택

### 4.4 관련 문서

- `docs/plan/ONNX_INFERENCE.md`
