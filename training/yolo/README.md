# training/yolo — 스크립트 요약

**전체 가이드(실행 전 설정 + 실행 순서): [`../README.md`](../README.md)**

| 파일 | 용도 |
|------|------|
| `train_segment.py` | 세그 학습 (**서비스 본선**) |
| `train_detect.py` | 박스 탐지 (실험) |
| `prepare_cutnkeep_seg.py` | coco128-seg → 5클래스 변환 (소량 스모크) |
| `prepare_coco5k_seg.py` | COCO train2017 → ~5000장 5클래스 + LoRA JSON |
| `apply_best.py` | best.pt → `models/yolo26s-seg.pt` + 샘플 추론 |
| `export_onnx.py` | `.pt` → `.onnx` |

## 실행 전 최소 체크

1. `python yolo/prepare_coco5k_seg.py --limit 5000` — COCO 5클래스 ~5k + `data/pseudo_labels`
2. `configs/dataset_seg.yaml` — yaml 기준 상대 `path` (`train_segment.py` 가 절대 경로로 해석)
3. `datasets/cutnkeep_seg_5k` — seg **폴리곤** 라벨
4. `backend/.../nodes.py` keywords 의 label = yaml `names` (소문자)
5. torch + ultralytics 가 training venv 에 설치됨

## 빠른 실행

```powershell
cd d:\my_project\CutNKeep\training
. .\env_cuda.ps1
.\.venv\Scripts\Activate.ps1

python yolo/train_segment.py --model yolo26s-seg.pt --data configs/dataset_seg.yaml --device 0
```

산출: `outputs/segment/<name>/weights/best.pt`  
→ `python yolo/apply_best.py` 가 `models/yolo26s-seg.pt` 로 복사 + 샘플 추론.  
`.env` `YOLO_MODEL_PATH=models/yolo26s-seg.pt` 후 backend 재시작.
