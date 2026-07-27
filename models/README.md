# models — 학습/추론 가중치

ONNX, PyTorch 체크포인트, (향후) LoRA 어댑터를 두는 곳이다.

## 권장 파일 (Phase 1)

| 파일 | 설명 |
|------|------|
| `yolo26n-seg.pt` | Ultralytics YOLO26n 인스턴스 세그 (로컬 추론) |
| `yolo26n-seg.onnx` | 배포·ONNX Runtime 용 export 산출물 |

```env
YOLO_MODEL_PATH=models/yolo26n-seg.pt
# 또는
# YOLO_MODEL_PATH=models/yolo26n-seg.onnx
```

## Git

- `*.pt`, `*.onnx`, `*.safetensors` 등은 **gitignore**  
- 디렉터리만 `.gitkeep` 으로 유지  

가중치는 직접 받거나 export 해서 이 폴더에 넣는다.

```powershell
# 예: ONNX 변환 (ultralytics 환경)
python scripts/convert_to_onnx.py --weights models/yolo26n-seg.pt --out models/yolo26n-seg.onnx
```

## Docker

Compose 는 `./models` → `/app/models` 마운트.  
경량 이미지에 torch 가 없으면 **ONNX + onnxruntime** 경로를 쓰는 편이 안전하다.

## 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/guidance/llm-and-vision.md`
