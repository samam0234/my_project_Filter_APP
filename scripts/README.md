# scripts — 유틸 · 학습 · 유지보수 스크립트

백엔드 런타임 밖에서도 돌리는 **오프라인/운영 보조** 스크립트 모음이다.

## 목록

| 스크립트 | 용도 |
|----------|------|
| `convert_to_onnx.py` | YOLO 가중치 → ONNX 변환 |
| `cleanup.py` | 오래된 업로드 임시 파일 삭제 (보관 시간) |
| `pseudo_labeling.py` | Phase 2 의사 라벨링 스캐폴드 |
| `fine_tune_lora.py` | Phase 2 LoRA 학습 스캐폴드 |
| `evaluate_model.py` | 모델 평가 스캐폴드 |

## 사용 예

```powershell
cd d:\my_project\CutNKeep

# 백엔드 venv 활성화 권장
.\backend\.venv\Scripts\activate

python scripts/convert_to_onnx.py --weights models/yolo26n-seg.pt --out models/yolo26n-seg.onnx
python scripts/cleanup.py
```

환경변수 `FILE_RETENTION_HOURS` 는 cleanup 에 영향 (기본 24).

## 주의

- Phase 2 스크립트는 **스캐폴드**일 수 있다. 실행 전 파일 상단 docstring 확인.
- 모델 파일(`.pt`, `.onnx`)은 용량 때문에 gitignore 대상이다. `models/` 에 직접 배치.

## 학습 구역 이전 안내

YOLO/LoRA **본 학습**은 `training/` 을 사용한다.

| 예전 (scripts) | 새 위치 |
|----------------|---------|
| `convert_to_onnx.py` | `training/yolo/export_onnx.py` |
| `fine_tune_lora.py` | `training/lora/train_lora.py` |
| (세그/디텍트 train) | `training/yolo/train_*.py` |

`scripts/` 의 cleanup 등 **운영 유틸**은 그대로 유지.

## 관련 문서

- `training/README.md`
- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/LOGIC_STRUCTURE.md` (피드백 → LoRA 루프)
