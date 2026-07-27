# training/yolo — 탐지 · 세그멘테이션 학습

Ultralytics YOLO 로 **object detection** / **instance segmentation** 을 학습한다.

## 스크립트

| 파일 | 용도 |
|------|------|
| `train_segment.py` | 세그 학습 (컷앤킵 메인 경로) |
| `train_detect.py` | 박스 탐지 학습 (보조/실험) |
| `export_onnx.py` | `.pt` → `.onnx` |

## 데이터 레이아웃 예

```text
training/datasets/my_seg/
  images/train/*.jpg
  images/val/*.jpg
  labels/train/*.txt   # seg: class + polygon 정규화
  labels/val/*.txt
```

config: `training/configs/dataset_seg.example.yaml` 복사 후 수정.

## 실행 예

```powershell
cd d:\my_project\CutNKeep\training
.\.venv\Scripts\activate

# 세그 (권장 시작: yolo26n-seg)
python yolo/train_segment.py --model yolo26n-seg.pt --data configs/dataset_seg.example.yaml --epochs 100

# 탐지
python yolo/train_detect.py --model yolo26n.pt --data configs/dataset_detect.example.yaml --epochs 100

# ONNX
python yolo/export_onnx.py --weights outputs/segment/exp/weights/best.pt --out ../models/yolo26n-seg.onnx
```

산출물 기본 위치: `training/outputs/` (프로젝트 설정에 따라 ultralytics runs 경로 사용 가능).

## 서비스 적용

1. `best.pt` → `models/yolo26n-seg.pt`  
2. `.env`: `YOLO_MODEL_PATH=models/yolo26n-seg.pt`  
3. backend 재시작  

자세한 전략: `docs/plan/AI_MODEL_STRATEGY.md`
