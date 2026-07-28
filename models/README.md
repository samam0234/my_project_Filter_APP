# models — 학습/추론 가중치

ONNX, PyTorch 체크포인트, (향후) LoRA 어댑터를 두는 곳이다.

## 【수동·필수】

- 이 폴더에 **직접 파일을 배치**해야 한다 (git 에 가중치 없음).
- 서비스 본선: **`yolo26s-seg.pt`** (또는 onnx) — **세그** 모델.
- detect 전용 `yolo26s.pt` 만 넣으면 마스크가 없어 stub 로 떨어질 수 있음.
- 경로: `.env` 의 `YOLO_MODEL_PATH` (기본 `models/yolo26s-seg.pt`).
- 학습 후: `training/outputs/.../best.pt` 를 여기로 **수동 복사**.

## 권장 파일 (Phase 1)

| 파일 | 설명 |
|------|------|
| `yolo26s-seg.pt` | Ultralytics YOLO26s 인스턴스 세그 (로컬 추론) |
| `yolo26s-seg.onnx` | 배포·ONNX Runtime 용 export 산출물 |

```env
YOLO_MODEL_PATH=models/yolo26s-seg.pt
# 또는
# YOLO_MODEL_PATH=models/yolo26s-seg.onnx
```

## Git

- `*.pt`, `*.onnx`, `*.safetensors` 등은 **gitignore**  
- 디렉터리만 `.gitkeep` 으로 유지  

가중치는 직접 받거나 export 해서 이 폴더에 넣는다.

```powershell
# 예: ONNX 변환 (ultralytics 환경)
python scripts/convert_to_onnx.py --weights models/yolo26s-seg.pt --out models/yolo26s-seg.onnx
```

## Docker

Compose 는 `./models` → `/app/models` 마운트.  
경량 이미지에 torch 가 없으면 **ONNX + onnxruntime** 경로를 쓰는 편이 안전하다.

## 학습은 어디서?

**`training/`** 폴더에서 YOLO detect/seg · LoRA 학습을 돌린 뒤,  
완성된 `best.pt` / `.onnx` 를 이 `models/` 로 복사해 서비스에 연결한다.

- `training/README.md`
- `training/yolo/README.md`

## 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/guidance/llm-and-vision.md`
