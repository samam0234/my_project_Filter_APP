# backend/models — 서빙 중인 활성 모델

백엔드가 **지금 실제로 로드하는** 가중치만 둔다.
원본·후보·LoRA 어댑터 보관소는 루트 [`models/`](../../models/README.md) 이다.

| 파일 | 설명 |
|------|------|
| `yolo26m-seg.pt` | 서빙 중인 YOLO 세그 가중치 (`YOLO_MODEL_PATH` 기본값) |
| `yolo26m-seg.onnx` | (선택) ONNX Runtime 서빙용 |
| `segformer-ade.onnx` · `segformer-ade.labels.json` | (선택) 건물·하늘·도로 같은 배경 덩어리용 SegFormer. `python scripts/export_stuff_onnx.py` 로 만든다 (`STUFF_MODEL_PATH`) |

## 배포 (교체)

```powershell
# 학습 best.pt → 여기로 복사 + 샘플 추론 확인
python training/yolo/apply_best.py

# 루트 보관소의 다른 후보로 교체
python training/yolo/apply_best.py --weights models/<후보>.pt --skip-predict
```

교체 후 backend 재시작. detect 전용 `.pt` 는 마스크가 없어 stub 로 떨어지니 넣지 말 것.

```env
YOLO_MODEL_PATH=models/yolo26m-seg.pt   # backend/ 기준
```

Docker: `./backend/models` → `/app/models` 마운트.
