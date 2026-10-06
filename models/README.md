# models — 모델 원본·후보 보관소

ONNX, PyTorch 체크포인트, LoRA 어댑터의 **원본과 후보**를 보관하는 곳이다.
백엔드가 실제로 로드하는 활성 모델은 [`backend/models/`](../backend/models/README.md) 에 따로 둔다.

## 【수동·필수】

- 이 폴더에 **직접 파일을 배치**해야 한다 (git 에 가중치 없음).
- 서비스 본선: **`yolo26m-seg.pt`** (또는 onnx) — **세그** 모델.
- detect 전용 `yolo26s.pt` 만 넣으면 마스크가 없어 stub 로 떨어질 수 있음.
- 서빙 반영: `python training/yolo/apply_best.py --weights models/<파일>` → `backend/models/` 로 배포.

## 권장 파일 (Phase 1)

| 파일 | 설명 |
|------|------|
| `yolo26m-seg.pt` | Ultralytics YOLO26m 인스턴스 세그 — 서빙 기본 (2026-10-06~) |
| `yolo26s-seg.pt` | YOLO26s 인스턴스 세그 (이전 기본, 가벼운 대안) |
| `yolo26m-seg.onnx` | 배포·ONNX Runtime 용 export 산출물 (ONNX predict 는 하드코딩 구간) |

## Git

- `*.pt`, `*.onnx`, `*.safetensors` 등은 **gitignore**  
- 디렉터리만 `.gitkeep` 으로 유지  

가중치는 직접 받거나 export 해서 이 폴더에 넣는다.

```powershell
# 예: ONNX 변환 (ultralytics 환경)
python scripts/convert_to_onnx.py --weights models/yolo26m-seg.pt --out models/yolo26m-seg.onnx
```

## Docker

Compose 는 이 폴더가 아니라 `./backend/models` → `/app/models` 를 마운트한다.  
경량 이미지에 torch 가 없으면 **ONNX + onnxruntime** 경로를 쓰는 편이 안전하다.

## 학습은 어디서?

**`training/`** 폴더에서 YOLO detect/seg · LoRA 학습을 돌린 뒤,  
완성된 `best.pt` / `.onnx` / LoRA `adapter/` 를 보관하고, 서빙할 것만 `backend/models/` 로 배포한다.

| 학습 산출 | 위치 |
|-----------|-----------|
| `training/outputs/segment/<name>/weights/best.pt` | `apply_best.py` → `backend/models/yolo26s-seg.pt` (보관 시 `models/` 에도 복사) |
| `training/outputs/lora/<run>/adapter/` | 보관은 여기, 서빙은 `backend/models/lora/` 로 복사 (`LLM_PROVIDER=lora`) |

- `training/README.md`
- `training/yolo/README.md`
- `training/lora/README.md`

## 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/guidance/llm-and-vision.md`
