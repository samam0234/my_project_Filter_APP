# backend/models — 지금 서빙 중인 모델

> 백엔드가 **실제로 로드하는** 가중치만 둔다. 원본 · 후보 보관소는 루트 [`models/`](../../models/README.md)다.

**가중치 파일은 Git에 없다.** 이 폴더에는 `.gitkeep`과 이 README만 추적된다. 새 서버나 새 PC에서는 직접 넣거나 받는다.

## 파일

| 파일 | 쓰는 곳 | 설정 | 없으면 |
|------|---------|------|--------|
| `yolo26m-seg.pt` | **서빙 기본** 인스턴스 세그 (2026-10-06~) | `YOLO_MODEL_PATH=models/yolo26m-seg.pt` | 가짜 마스크(stub)로 데모만 됨 |
| `yolo26m-seg.onnx` | (선택) torch 없이 ONNX Runtime으로 서빙 — Docker `SEG_RUNTIME=onnx` | `YOLO_MODEL_PATH=models/yolo26m-seg.onnx` | |
| `lama_fp32.onnx` | 대상 지우기의 빈자리 메우기 LaMa (Apache-2.0, 208MB, SHA-256 `1faef530…68d6`) | `INPAINT_MODEL_PATH` | **기동 시 자동으로 받는다** (`MODEL_AUTO_DOWNLOAD=true`, 체크섬 확인). 받는 동안은 Telea |
| `segformer-ade.onnx` · `segformer-ade.labels.json` | (선택) 건물 · 하늘 · 도로 같은 배경 덩어리 14종 | `STUFF_MODEL_PATH` | 배경 덩어리 문장만 동작하지 않음 |
| `lora/` | (선택) LoRA 어댑터 — `LLM_PROVIDER=lora` 또는 `PROMPT_SECOND_OPINION` | `LORA_ADAPTER_PATH` | Ollama · 키워드 파서로 해석 |
| `qwen2.5-1.5b-instruct/` | (선택) LoRA 베이스 모델 (HF 형식 폴더) | `LORA_BASE_MODEL` | |
| `lora_prev_*/` | `retrain_lora.py --deploy`가 교체 전에 남긴 이전 어댑터 | | |

`yolo26s-seg.pt` · `yolo26l-seg.pt` · `yolo26x-seg.pt`처럼 다른 크기를 같이 둘 수 있다. `yolo26x`는 `scripts/seg_labeling.py`의 초벌 폴리곤에 쓴다.

**detect 전용 `.pt`를 넣지 않는다.** 마스크가 없는 가중치라 세그가 stub로 떨어진다. 요청 대상이 라벨에 없으면 stub로 속이지 않고 실패로 알린다.

## 받기 · 만들기

```bash
python scripts/fetch_models.py                       # LaMa (손으로 받을 때)
docker exec cut_and_keep-backend-1 python -m app.services.model_fetch   # Docker 안에서
python scripts/convert_to_onnx.py --weights models/yolo26m-seg.pt --out models/yolo26m-seg.onnx
python scripts/export_stuff_onnx.py                  # SegFormer → segformer-ade.onnx
```

서버로 옮길 때는 `python scripts/models_bundle.py pack`으로 설정이 쓰는 모델만 묶고, 서버에서 `verify`로 체크섬을 대조한다.

## 교체

```bash
# 학습 best.pt → 여기로 복사 + 샘플 추론 확인
python training/yolo/apply_best.py --weights training/outputs/segment/<run>/weights/best.pt --dest backend/models/yolo26m-seg.pt

# 루트 보관소의 다른 후보로 교체
python training/yolo/apply_best.py --weights models/<후보>.pt --dest backend/models/yolo26m-seg.pt --skip-predict
```

`apply_best.py`의 기본 대상 파일명은 아직 `yolo26s-seg.pt`다. 서빙 기본(m)을 바꾸려면 `--dest`를 지정하거나 `YOLO_MODEL_PATH`를 그 파일로 맞춘다. 교체 후 백엔드를 다시 시작한다.

## Docker

`./backend/models` → `/app/models` 마운트. GPU 오버레이는 LoRA 베이스 모델을 호스트 폴더(`LORA_BASE_DIR`)에서 읽기 전용으로 붙인다.
