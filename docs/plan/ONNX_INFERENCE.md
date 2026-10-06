# ONNX 세그 추론 (torch·ultralytics 없이)

**일자:** 2026-10-06 · **브랜치:** `feature/onnx-infer`
`.onnx` 가중치를 onnxruntime 만으로 돌린다. 전처리·후처리를 직접 구현했다 (`backend/app/utils/onnx_utils.py`).

## 1. 왜

Docker 이미지가 세그를 돌리려고 CPU 용 torch + ultralytics 를 넣으면 **2.81 GB** 다.
onnxruntime 만 쓰면 **1.11 GB** — 배포 서버(Oracle Cloud 등)에서 받고 올리는 시간·디스크가 줄어든다.

| 이미지 | 크기 | 세그 (Docker CPU, m) |
|--------|------|----------------------|
| `SEG_RUNTIME=ultralytics` (기본, `.pt`) | 2.81 GB | 225~345 ms |
| `SEG_RUNTIME=onnx` (`.onnx`) | **1.11 GB** | 250~310 ms |

슬림 컨테이너(torch · ultralytics 없음)로 실제 업로드 6건 모두 정상 (`ultralytics False · torch False · onnxruntime True`).

## 2. 쓰는 법

```powershell
# 1) .pt → .onnx (한 번, ultralytics 환경. YOLO_AUTOINSTALL=False 권장 — 아래 주의)
python -c "from ultralytics import YOLO; YOLO('backend/models/yolo26m-seg.pt').export(format='onnx', imgsz=640)"
#    → backend/models/yolo26m-seg.onnx (90 MB, git 무시)

# 2) 로컬: .env
YOLO_MODEL_PATH=models/yolo26m-seg.onnx
SEG_PREFER_ONNX=true        # ultralytics 가 설치돼 있어도 onnxruntime 으로 (없으면 자동으로 onnx 경로)

# 3) Docker 슬림 이미지
SEG_RUNTIME=onnx docker compose -p cut_and_keep --env-file .env up -d --build backend
#    (.env 의 YOLO_MODEL_PATH 도 .onnx 로)
```

기동 로그 `ONNX 모델 로드`, 결과 `backend=onnx`.

## 3. 구현 (`onnx_utils.py`)

모델 입출력 (Ultralytics export): 입력 `images [1,3,640,640]` RGB 0~1, 출력 `output0 [1,116,8400]`
(cx·cy·w·h + 클래스 80 + 마스크 계수 32, **NMS 없음**), `output1 [1,32,160,160]` 마스크 원형.

1. `letterbox` — 비율 유지 축소 + 가운데 회색(114) 패딩
2. `preprocess` — BGR → RGB, NCHW, /255
3. `postprocess` — 신뢰도 필터 → **클래스별 NMS**(IoU 0.7) → 계수 × proto →
   proto 격자에서 패딩 제거 → **원본 크기로 확대 → 그 해상도에서 박스로 자름** → 로짓 > 0
4. `class_names` — ONNX 메타데이터 `names` (없으면 숫자)
5. `Segmentor._predict_onnx` — 요청 대상 라벨만 모아 `.pt` 경로와 같은 `SegmentationResult` (`backend="onnx"`)

재시도의 낮춘 신뢰도(`min_confidence`)는 출력 단계에서 바로 적용된다 (ONNX 에는 `conf=` 인자가 없어서).

## 4. 검증 (COCO val2017)

| 비교 | 마스크 IoU 평균 | 중앙값 | 측정 |
|------|----------------|--------|------|
| 내 구현 vs Ultralytics 가 같은 ONNX 를 돌린 결과 | **0.973** | **1.000** | 100장, 일회성 점검 스크립트 |
| 내 구현 vs `.pt` (정밀 마스크) | 0.928 | 0.979 | 200장, `scripts/experiments/onnx_vs_pt.py` |

정답 폴리곤과의 경계 IoU (IoU≥0.5 로 찾은 인스턴스):

| 방식 | 평균 |
|------|------|
| `.pt` 단순 확대 (**이전 백엔드**) | 0.825 |
| `.pt` 정밀(retina) | 0.848 |
| 내 ONNX | 0.848 |
| Ultralytics ONNX 정밀 | 0.846 |

200장 검출률 `.pt` 88.8% · ONNX 89.3%, 위치 선택 정확도 81.1% · 81.5% — 사실상 같다 (`onnx_vs_pt.py`).
`.pt` 와 ONNX 의 검출 수가 조금 다른 건(727 vs 740) 입력 방식 차이(`.pt` 는 stride 맞춘 직사각형, ONNX 는 640 정사각 letterbox).

### 처음 구현의 문제 (기록)

처음엔 박스로 자르기를 160 격자에서 먼저 했다 → 가장자리가 거칠어 Ultralytics 와 IoU 0.89.
정밀 방식(원본 크기로 확대한 뒤 자름)으로 바꿔 0.973. 비교 기준도 두 번 틀렸다:
`masks.data` 를 그대로 늘리면 letterbox 패딩 때문에 어긋나고, `masks.xy` 폴리곤은 가장 큰 윤곽선만 남긴다 →
**`retina_masks=True` 마스크**가 맞는 기준.

## 5. 같이 고친 것 — `.pt` 경로의 거친 마스크

위 표의 "이전 백엔드" 가 `.pt` 경로였다. letterbox 크기 마스크를 단순 확대해 경계가 거칠었다 (정답 대비 IoU 0.825).
`predict(retina_masks=True)` 로 원본 해상도에서 바로 계산 → **0.848**, 속도 차이 없음(워밍업 후 19 vs 20 ms).

## 6. 주의 · 한계

- **Ultralytics 자동 설치**: `.onnx` 를 `YOLO(...)` 로 열면 `onnxruntime-gpu` 를 자동 설치해 기존 `onnxruntime` 을
  깨뜨린다 (이번 작업 중 학습 venv 에서 발생, `pip install --force-reinstall onnxruntime==1.19.2` 로 복구).
  실험 스크립트 실행 시 `YOLO_AUTOINSTALL=False` 를 건다. 백엔드 코드는 `.onnx` 를 ultralytics 로 열지 않는다(`SEG_PREFER_ONNX`) 
- **속도**: Docker CPU 에서는 세그 250~310 ms 로 ultralytics CPU 와 비슷하지만, 이 Windows PC(onnxruntime 1.19.2 CPU)에서는
  `onnx_vs_pt.py` 기준 장당 약 1.1 s 로 느렸다 (`.pt` 는 GPU 155 ms 라 직접 비교 불가). 환경마다 다르니 배포 서버에서 다시 잴 것
- 입력 640 고정 export. 동적 크기 모델은 `input_size` 가 640 으로 대체
- CPU 만 (`providers` 기본). GPU onnxruntime 은 배포 환경 결정 후
- 클래스 이름은 ONNX 메타데이터에 의존 — 직접 만든 export 는 `names` 가 들어 있는지 확인
