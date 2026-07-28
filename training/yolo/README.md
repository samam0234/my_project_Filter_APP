# training/yolo — 스크립트 요약

**전체 가이드(실행 전 설정 + 실행 순서): [`../README.md`](../README.md)**

| 파일 | 용도 |
|------|------|
| `train_segment.py` | 세그 학습 (**서비스 본선**) |
| `train_detect.py` | 박스 탐지 (실험) |
| `export_onnx.py` | `.pt` → `.onnx` |

## 실행 전 최소 체크

1. `configs/dataset_seg.yaml` — `path` / **`names`** (클래스 이름)
2. `datasets/...` — seg **폴리곤** 라벨 (detect bbox 와 다름)
3. `backend/.../nodes.py` keywords 의 label = yaml `names` (소문자)
4. torch + ultralytics 가 training venv 에 설치됨

## 빠른 실행

```powershell
cd d:\my_project\CutNKeep\training
. .\env_cuda.ps1
.\.venv\Scripts\Activate.ps1

python yolo/train_segment.py --model yolo26s-seg.pt --data configs/dataset_seg.yaml --device 0
```

산출: `outputs/segment/<name>/weights/best.pt`  
→ `models/yolo26s-seg.pt` 복사 후 `.env` `YOLO_MODEL_PATH` → backend 재시작.
