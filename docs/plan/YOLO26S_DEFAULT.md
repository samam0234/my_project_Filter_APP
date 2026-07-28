# 비전 기본 모델: YOLO26n → YOLO26s 전환

**일자:** 2026-07-28  
**브랜치:** `feature/backend`  
**대상:** Phase 1 기본 비전 스케일을 **nano(n) → small(s)** 로 통일

---

## 1. 왜 바꿨나

| 항목 | n (기존 문서 기본) | s (현재 기본) |
|------|-------------------|---------------|
| 스케일 | nano — 가장 가벼움 | small — 품질·속도 균형 |
| 마스크 품질 | 빠름, 경계·소객체에 약할 수 있음 | 표현력 증가, 컷앤킵 마스크에 유리 |
| 리소스 | CPU/저사양에 유리 | 로컬 GPU·개발 PC 기준 현실적 |
| 학습 스크립트 기본 | (과거) n 언급 | **`yolo26s-seg.pt` / `yolo26s.pt`** |

서비스 본선은 여전히 **instance segmentation (`*-seg`)**.  
detection (`yolo26s.pt`) 은 학습·검수·실험용.

---

## 2. 파일 이름 매핑

| 용도 | 이전 (문서상) | **현재 기본** |
|------|---------------|---------------|
| 세그 사전학습 / 서빙 | `yolo26n-seg.pt` | **`yolo26s-seg.pt`** |
| 세그 ONNX | `yolo26n-seg.onnx` | **`yolo26s-seg.onnx`** |
| 탐지 사전학습 | `yolo26n.pt` | **`yolo26s.pt`** |
| `.env` | `YOLO_MODEL_PATH=models/yolo26n-seg.pt` | **`models/yolo26s-seg.pt`** |

코드 기본값: `backend/app/core/config.py` → `YOLO_MODEL_PATH` default.  
학습 기본: `training/yolo/train_segment.py` / `train_detect.py` CLI `--model`.

---

## 3. 동기화된 문서·설정 (체크리스트)

- [x] `.env.example`
- [x] `backend/app/core/config.py`
- [x] `models/README.md`
- [x] `training/yolo/*`, `training/README.md`, `training/configs/*`
- [x] `docs/plan/AI_MODEL_STRATEGY.md`
- [x] `docs/plan/LOGIC_STRUCTURE.md`
- [x] `docs/plan/PROJECT_STRUCTURE.md`, `TESTING.md`, `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`
- [x] `docs/guidance/llm-and-vision.md`
- [x] `AGENTS.md`, 스킬/규칙 요약
- [x] `RUN.md`, 루트 `README.md`
- [x] `scripts/convert_to_onnx.py`, `scripts/README.md`

로컬에 이미 `yolo26n-seg.pt` 만 있다면:

1. s 가중치를 받거나 학습하거나  
2. 당분간 `.env` 에 `YOLO_MODEL_PATH=models/yolo26n-seg.pt` 로 **경로만** n 유지 가능 (파이프라인 동일)

---

## 4. 개발자 할 일

```text
1) models/yolo26s-seg.pt 배치 (또는 학습 best.pt 복사·이름 변경)
2) .env YOLO_MODEL_PATH=models/yolo26s-seg.pt
3) backend 재시작 → 로그 "YOLO 세그멘터 준비" / meta.backend=yolo
4) (학습) training venv 에서 train_segment.py --model yolo26s-seg.pt
5) (탐지 실험) train_detect.py --model yolo26s.pt
```

---

## 5. 관련 코드의 【수동】 주석

동일 패치에서 사용자가 직접 설정·구현할 지점에 `【수동】` 주석을 달았다.  
인덱스는 로컬 `Scribble/note.md` 섹션 E 참고.

---

**요약:** 문서·설정·학습 기본 진입점은 **YOLO26s / YOLO26s-seg**.  
n 은 경량 옵션으로 경로 교체만 하면 된다.
