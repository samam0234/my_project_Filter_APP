# training/lora — 피드백 기반 LoRA (Phase 2)

사용자/파이프라인 피드백(`data/feedback/`)과 의사 라벨을 이용해  
**가벼운 추가 학습(LoRA)** 을 돌리는 구역이다.

## 현재 상태

- **스캐폴드**: `train_lora.py` 는 입출력 계약과 TODO 를 정의한 단계
- Phase 1 에서는 YOLO fine-tune (`training/yolo/`) 을 우선

## 예정 흐름

```text
data/feedback/*.jpg + *.json
        ↓
pseudo label (Grounding DINO+SAM2 등) → training/datasets/ 또는 data/pseudo_labels/
        ↓
train_lora.py  (PEFT / 도메인 어댑터)
        ↓
outputs/lora/adapter 또는 safetensors
        ↓
서버에 어댑터 교체 (전체 모델 재배포 최소화)
```

## 실행 (Phase 2 준비 후)

```powershell
cd training
.\.venv\Scripts\activate
# pip install peft transformers accelerate  # requirements-training.txt 주석 해제
python lora/train_lora.py --help
```

## 관련

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/LOGIC_STRUCTURE.md` (피드백 루프)
- `scripts/fine_tune_lora.py` (레거시 스캐폴드)
