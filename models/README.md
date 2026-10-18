# models — 가중치 원본 · 후보 보관소

> 학습했거나 받은 가중치의 **원본과 후보**를 두는 곳. 백엔드가 지금 로드하는 것은 [`backend/models/`](../backend/models/README.md)에 따로 둔다.

두 폴더를 나눈 이유는 **보관과 서빙을 섞지 않기 위해서**다. 후보를 여기 쌓아 두고 비교한 뒤, 이긴 것만 `backend/models/`로 옮긴다.

```text
training/outputs/…/best.pt ──보관──▶ models/<이름>.pt ──채택──▶ backend/models/yolo26m-seg.pt ──▶ 백엔드 재시작
training/outputs/lora/<run>/adapter/ ─────────────────────────▶ backend/models/lora/
```

## 【수동 · 필수】

- **가중치는 Git에 없다.** `*.pt` · `*.onnx` · `*.safetensors` 등은 ignore이고, 폴더는 `.gitkeep`으로만 유지한다. 직접 받거나 학습 · 변환해서 넣는다.
- 서비스 본선은 **세그(segment) 모델**이다 — `yolo26m-seg.pt`(또는 `.onnx`).
- detect 전용 `yolo26s.pt`만 넣으면 마스크가 없어 세그가 가짜 마스크(stub)로 떨어진다.

## 권장 파일

| 파일 | 설명 |
|------|------|
| `yolo26m-seg.pt` | Ultralytics YOLO26m 인스턴스 세그 — **서빙 기본** (2026-10-06~). s → m 전환 근거: [`docs/plan/YOLO26M_DEFAULT.md`](../docs/plan/YOLO26M_DEFAULT.md) |
| `yolo26s-seg.pt` | YOLO26s 인스턴스 세그 — 이전 기본, 가벼운 대안. 학습 스크립트의 출발 가중치로도 쓴다 |
| `yolo26m-seg.onnx` | 배포 · ONNX Runtime용 내보내기 — torch 없이 추론 ([`docs/plan/ONNX_INFERENCE.md`](../docs/plan/ONNX_INFERENCE.md)) |
| LoRA `adapter/` | Qwen2.5-1.5B 문장 해석 어댑터 후보 |

학습 스크립트의 출발 가중치가 `yolo26s-seg.pt`인 것과 서빙 기본이 m인 것은 별개다.

## 만들기 · 옮기기

```bash
# ONNX 변환 (ultralytics 환경)
python scripts/convert_to_onnx.py --weights models/yolo26m-seg.pt --out models/yolo26m-seg.onnx

# 후보를 서빙으로 (샘플 추론으로 확인) — 기본 대상 이름이 yolo26s-seg.pt 라 --dest 를 지정한다
python training/yolo/apply_best.py --weights models/<후보>.pt --dest backend/models/yolo26m-seg.pt

# 서버로 옮길 때 — 설정이 쓰는 모델만 묶고 체크섬 목록
python scripts/models_bundle.py pack
```

재학습 루프(`scripts/retrain_yolo.py` · `scripts/retrain_lora.py`)는 후보를 배포 중인 모델과 비교해 **나아졌을 때만** 교체한다. COCO만 추가한 세그 재학습은 채택되지 않았다.

## Docker

Compose는 이 폴더가 아니라 `./backend/models` → `/app/models`를 마운트한다.
가벼운 이미지(`SEG_RUNTIME=onnx`)는 torch 없이 onnxruntime으로 `.onnx`를 쓴다 — 이미지 약 2.8GB → 약 1.1GB.

## 학습 산출물의 위치

| 학습 산출 | 보관 | 서빙 |
|-----------|------|------|
| `training/outputs/segment/<name>/weights/best.pt` | 여기 `models/`에 복사 | `apply_best.py --dest backend/models/yolo26m-seg.pt` |
| `training/outputs/lora/<run>/adapter/` | 그 자리 또는 여기 | `backend/models/lora/` 로 복사 (`LLM_PROVIDER=lora`) |

## 관련 문서

- [`training/README.md`](../training/README.md) · [`training/yolo/README.md`](../training/yolo/README.md) · [`training/lora/README.md`](../training/lora/README.md)
- [`docs/plan/AI_MODEL_STRATEGY.md`](../docs/plan/AI_MODEL_STRATEGY.md)
- [`docs/guidance/llm-and-vision.md`](../docs/guidance/llm-and-vision.md)
