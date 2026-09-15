# training/lora — 피드백 기반 LoRA (Phase 2)

사용자/파이프라인 피드백(`data/feedback/`)과 의사 라벨을 이용해
**프롬프트 분석기용 가벼운 어댑터(LoRA)** 를 돌리는 구역이다.

세그 마스크 품질은 **`training/yolo/`** (YOLO-seg fine-tune) 가 본선이다.
여기는 ParsedPrompt JSON 을 더 잘 뽑기 위한 **Causal LM 어댑터** 다.

## 현재 상태

- **데이터 계약 + dry-run**: torch/peft 없이 동작
- **학습 본선**: 로컬 HF 체크포인트 + peft 가 있을 때 adapter 저장
- 하드코딩 숙제: instruction 템플릿 · vote 정책 · `--target-modules` (비우면 바이브 기본값)

## 예정 흐름

```text
data/feedback/*.jpg + *.json   (prompt, parsed_prompt, vote)
        ↓
(선택) data/pseudo_labels/*.json
        ↓
train_lora.py  --dry-run     ← 레코드 수·스키마 확인
        ↓
train_lora.py  --base-model <로컬 HF>
        ↓
outputs/lora/<run>/adapter/  + run.json
        ↓
(수동) models/lora/ 복사 — 서버 핫스왑은 후속
```

## 실행 전 — 맞춰야 할 것

### 1) 피드백 JSON 에 정답이 있는가

학습 레코드는 **prompt + ParsedPrompt** 가 있을 때만 만들어진다.

| vote / source | 정답으로 쓰는 것 |
|---------------|------------------|
| `like` | `meta.parsed_prompt` |
| `pipeline_failure` | `meta.parsed_prompt` (약한 정답, `--skip-pipeline-failure` 로 제외) |
| `dislike` | **코멘트가 ParsedPrompt JSON 일 때만** (시스템 출력은 오답) |
| `pseudo_labels` | 같은 키의 `parsed_prompt` |

최소 예:

```json
{
  "case_id": "job1_abcd1234",
  "vote": "like",
  "comment": null,
  "source": "user",
  "image": "job1_abcd1234.jpg",
  "meta": {
    "prompt": "강아지만 남기고 배경 블러",
    "parsed_prompt": {
      "target": ["dog"],
      "effect": "blur",
      "intensity": 15,
      "crop": false
    }
  }
}
```

`python training/lora/train_lora.py --dry-run` 으로 `records` 가 0 이 아닌지 먼저 본다.

### 2) 베이스 모델 (학습할 때만)

`--base-model` 은 **로컬 HuggingFace 디렉터리** (`config.json` + 가중치).

- **Ollama `gemma4:e4b` GGUF 는 PEFT 에 바로 못 씀**
- 허브에서 2GB+ 를 몰래 받지 않는다 (`local_files_only`)
- 추론 LLM(Ollama) 과 학습 체크포인트는 파일이 달라도 된다

### 3) 의존성 (학습할 때만)

```powershell
cd training
.\.venv\Scripts\Activate.ps1
pip install peft transformers accelerate
# torch 는 YOLO 와 같이 로컬 wheel
```

`requirements-training.txt` 의 LoRA 줄은 주석이다. 필요할 때 직접 설치.

## 실행

```powershell
cd training
.\.venv\Scripts\Activate.ps1

# 1) 데이터만 검증 (peft 불필요)
python lora/train_lora.py --dry-run

# 2) 학습
python lora/train_lora.py `
  --base-model D:\models\gemma-2-2b-it `
  --epochs 3 `
  --rank 8 `
  --device cuda
```

운영 래퍼 (주간 기본 인자 포함):

```powershell
python ..\scripts\fine_tune_lora.py --dry-run
python ..\scripts\fine_tune_lora.py --base-model D:\models\gemma-2-2b-it
```

## 산출

```text
training/outputs/lora/<run>/
  adapter/     ← peft save_pretrained (어댑터만)
  run.json     ← 샘플·하이퍼·경로 메타
```

적용: `adapter/` 를 `models/lora/` 로 **수동 복사**. backend 로드는 Phase 2 후속.

## 하지 않는 것

- YOLO-seg `best.pt` 학습 (→ `training/yolo/train_segment.py`)
- Grounding DINO + SAM2 마스크 LoRA (의사 라벨 루프가 먼저)
- Ollama GGUF 직접 fine-tune
- 허브 모델 자동 다운로드

## 관련

- `training/configs/lora.example.yaml` — 하이퍼 메모
- `docs/plan/LOGIC_STRUCTURE.md` — 피드백 → LoRA 루프
- `docs/plan/HARDCODING_ZONES.md` — 남은 숙제(템플릿·모듈)
- `scripts/fine_tune_lora.py` — 주간 배치 래퍼
