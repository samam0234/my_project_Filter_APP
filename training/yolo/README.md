# training/yolo — 세그 · 탐지 학습 스크립트

> YOLO 세그 모델을 학습하고, 결과를 서빙 폴더로 옮기는 스크립트. **실행 전 설정과 전체 순서는 [`../README.md`](../README.md)** 에 있다.

서비스 본선은 **인스턴스 세그(segment)** 다. 박스 탐지(detect)는 실험용이고, detect 가중치를 서빙에 넣으면 마스크가 없어 세그가 stub로 떨어진다.

## 스크립트

| 파일 | 용도 |
|------|------|
| `train_segment.py` | 세그 학습 (**서비스 본선**) — 산출 `training/outputs/segment/<name>/weights/best.pt` |
| `train_detect.py` | 박스 탐지 (실험) |
| `prepare_cutnkeep_seg.py` | coco128-seg → 5클래스 변환 (소량 스모크) |
| `prepare_coco5k_seg.py` | COCO train2017 → 약 5,000장 5클래스 + LoRA JSON (`data/pseudo_labels`) |
| `apply_best.py` | `best.pt` → 서빙 폴더로 복사 + 샘플 추론 확인 (`--weights` · `--dest` · `--image` · `--skip-predict`) |
| `export_onnx.py` | `.pt` → `.onnx` (torch 없이 서빙할 때) |
| [`../../scripts/retrain_yolo.py`](../../scripts/README.md#4-재학습-루프) | **재학습 루프** — 어려운 사례 수집 → 서비스 모델(80클래스)에서 이어 학습 → 섞임 평가 · mask mAP로 배포 모델과 비교 → 판정 → `--deploy` |

## 지금 서빙 모델과의 관계

| 항목 | 값 |
|------|----|
| 서빙 기본 | `backend/models/yolo26m-seg.pt` — COCO 80클래스 사전학습 (2026-10-06 s → m, [`docs/plan/YOLO26M_DEFAULT.md`](../../docs/plan/YOLO26M_DEFAULT.md)) |
| 학습 출발 가중치 | `yolo26s-seg.pt`일 수 있다 — 서빙 기본이 m인 것과 별개 |
| `apply_best.py` 기본 대상 | **`backend/models/yolo26s-seg.pt`** — 서빙 기본(m)을 바꾸려면 `--dest backend/models/yolo26m-seg.pt` 또는 `YOLO_MODEL_PATH`를 그 파일로 |

5클래스 직접 학습은 초기(Phase 1) 방식이다. 지금 서비스 모델은 이미 COCO로 학습되어 있어, COCO만으로 이어 학습한 실행은 두 번 모두 채택되지 않았다 ([`docs/vaildates/yolo-retrain-20261009.md`](../../docs/vaildates/yolo-retrain-20261009.md)). **COCO 밖의 실패 사진**이 쌓인 뒤의 재학습이 의미가 있다 — `scripts/seg_labeling.py`로 라벨링해 `retrain_yolo.py --extra`로 넣는다.

## 실행 전 최소 체크

1. `python yolo/prepare_coco5k_seg.py --limit 5000` — COCO 5클래스 약 5k + `data/pseudo_labels`
2. `configs/dataset_seg.yaml` — yaml 기준 상대 `path` (`train_segment.py`가 절대 경로로 해석)
3. `datasets/cutnkeep_seg_5k` — seg **폴리곤** 라벨
4. 백엔드 키워드의 label = yaml `names` (소문자)
5. torch + ultralytics가 training venv에 설치됨 (`../requirements-training.txt`)

## 빠른 실행

```powershell
cd training
. .\env_cuda.ps1
.\.venv\Scripts\Activate.ps1

python yolo/train_segment.py --model yolo26s-seg.pt --data configs/dataset_seg.yaml --device 0
```

```powershell
# 저장소 루트에서 — 결과를 서빙 폴더로 (서빙 기본 m 을 교체할 때)
python training/yolo/apply_best.py --weights training/outputs/segment/<name>/weights/best.pt --dest backend/models/yolo26m-seg.pt
```

교체 후 백엔드를 다시 시작한다. 원본 · 후보는 루트 [`models/`](../../models/README.md)에 보관한다.

## 관련 문서

- [`../README.md`](../README.md) — 학습 구역 전체 가이드
- [`../../backend/models/README.md`](../../backend/models/README.md) — 서빙 중인 모델
- [`../../docs/plan/AI_MODEL_STRATEGY.md`](../../docs/plan/AI_MODEL_STRATEGY.md)
