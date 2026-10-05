# training/lora — 프롬프트 분석 LoRA

자연어 요청을 `ParsedPrompt` JSON(대상·효과·**인스턴스 선택자**)으로 바꾸는
작은 모델(Qwen2.5-1.5B-Instruct)용 **LoRA 어댑터**를 학습·평가하는 구역이다.

세그 마스크 품질은 **`training/yolo/`** (YOLO-seg) 가 본선이다.
"맨 앞 빨간 안전모 남자" 중 **어느 인스턴스인지 고르는 것**은 학습이 아니라
`backend/app/services/instance_selector.py` 의 규칙이 한다. LoRA 는 그 규칙에 넣을
selector(위치·순서·개수·색 속성)를 **문장에서 정확히 뽑는 것**을 배운다.

## 흐름

```text
seed/build_seed.py ──→ seed/train.jsonl   (인스턴스 선택·물체 지우기 시드, 결정적 생성)
서비스 사용 ──→ 학습 DB learning_samples   (회원 요청 · 사용자 교정 · 좋아요)
        ↓  운영 콘솔 "학습 데이터" 검수 (승인 · 정답 고쳐서 승인 · 거절)
승인 문장 (train split) ──→ augment_prompts.py → outputs/lora/augment/approved_aug.jsonl
                                               (같은 뜻 다른 표현 · 자기 일치 검증)
data/pseudo_labels/*.json                  (단순 "X만 크롭" 계열 — 샘플링)
        ↓  dataset.py  (정답을 backend prompt_spec 으로 정규화 = 서빙과 같은 형식, 평가셋 문장 제외)
train_lora.py  --dry-run                   ← 레코드 수 확인
train_lora.py  --base-model …              → outputs/lora/<run>/adapter/
        ↓
eval_parser.py --adapter …                 ← seed/eval.jsonl 로 heuristic·ollama·base·lora 비교
eval_parser.py --eval-source db-val …      ← 승인된 실제 문장 중 val split (학습에 안 쓴 문장)
        ↓
backend/models/lora/ 로 복사 + .env LLM_PROVIDER=lora  (backend 재시작)
```

## 규격은 한 곳에서

`backend/app/services/prompt_spec.py`

| 이름 | 용도 |
|------|------|
| `LORA_TEMPLATE` | 학습 입력 = 서빙 입력 (바꾸면 재학습) |
| `normalize_parsed` / `parsed_to_json` | 정답 레이블 정규화 · 직렬화 |
| `SYSTEM_PROMPT` | Ollama/OpenAI/Gemini few-shot (LoRA 는 짧은 템플릿 사용) |

## 데이터 정책 (`train_lora.py`)

| 출처 | 정답 | 비고 |
|------|------|------|
| `seed/train.jsonl` | 그대로 | `--seed-repeat 2` 로 비중 확보 |
| **학습 DB 승인 문장** (기본 `--feedback-source db`) | 운영자가 검수한 `answer` | train split 만, `--approved-repeat 3` (수가 적어 시드에 묻히지 않게) |
| **증강** `--augment-file` | 원 문장의 검수된 정답 그대로 | 다른 표현 중 서비스 파서가 같은 정답을 내는 것만 (뜻 바뀐 표현 제거) |
| `pseudo_labels` | `parsed_prompt` | `--max-pseudo 600` 샘플링 (selector 학습 희석 방지) |
| (`--feedback-source files`) 사이드카 like / dislike+JSON / pipeline_failure | 검수 없음 | 예전 방식. 학습 DB 를 쓸 수 없을 때만 |

- **평가셋 문장은 학습에서 뺀다** (`--eval-file`, 공백·대소문자 무시). 원문이 평가셋 문장이면 증강도 하지 않는다
  - 2026-10-06 점검에서 의사 라벨 32건이 평가 문장 "사람만 남기고 배경 블러" 와 같았다 → v2 까지는 이 1문항(2.5%p)이 누수

- 문장에 숫자가 없으면 `intensity` 는 15 로 맞춘다 (의사 라벨의 "블러=20" 노이즈 제거)
- 응답 JSON 토큰에만 loss (지시문 암기 방지), 끝에 EOS
- `count` 규칙: 숫자 표현이나 위치 단어가 있을 때만. 명사만("남자") 으로는 채우지 않는다

### 사용자 문장을 정답으로 넣는 법

1. 회원이 쓴 요청은 자동으로 검수 후보(`request`)가 되고, 결과 화면 "정답 알려주기"는 교정 후보(`correction`)가 된다
2. 운영 콘솔 "학습 데이터"에서 승인 (해석이 틀렸으면 정답을 고쳐서 승인)
3. `augment_prompts.py` → `train_lora.py` → `eval_parser.py` (아래 실행)

교정 JSON 예 (콘솔에서 고칠 때도 같은 형식):

```json
{"target":["person"],"effect":"remove_bg","selector":{"position":"front","count":1,"attributes":["red helmet","neon yellow vest"]}}
```

## 실행

```powershell
# 저장소 루트, training venv
training\.venv\Scripts\Activate.ps1

python training/lora/seed/build_seed.py                # 시드 재생성 (선택)
python training/lora/train_lora.py --dry-run
python training/lora/augment_prompts.py --per-sample 8      # 승인 문장 증강 (Ollama 필요, 문장당 약 1분)
python training/lora/train_lora.py --base-model training/models/qwen2.5-1.5b-instruct --name instance_v1
python training/lora/eval_parser.py --adapter training/outputs/lora/instance_v1/adapter --report training/outputs/lora/instance_v1/eval.json

# 주간 래퍼 (기본 하이퍼 고정)
python scripts/fine_tune_lora.py --name weekly_YYMMDD
```

기본 하이퍼: epochs 3 · lr 2e-4 · rank 16 · batch 4 × grad-accum 2 · q/k/v/o_proj ·
bf16 (LoRA 가중치만 fp32) · gradient checkpointing (Ollama·백엔드와 GPU 공유 시 OOM 방지)

## 평가 (`eval_parser.py`)

`seed/eval.jsonl` 40건은 **생성기 템플릿과 다른 말투로 손으로 쓴** 평가셋이다
(사용자 실제 요청 포함). 속성은 문자열이 아니라 선택기가 해석하는 (색, 부위) 로 비교한다
— "fluorescent vest" 와 "neon yellow vest" 는 같은 동작이라 같은 답으로 본다.

### 확장 평가셋 · 사용자 문장 학습 (2026-10-06)

`seed/eval_ext.jsonl` 56건 — 기존 40건과 다른 말투(오타·띄어쓰기·구어·영어 혼용·남김/지움 헷갈리는 표현)와
새 대상(화분·꽃병·곰인형·기차·피자 …). 학습 데이터·기존 평가셋과 겹치는 문장 없음.
라벨이 애매한 4건(“사람들 다”, 색 없는 “모자 쓴 사람” 등)은 만들고 나서 뺐다.

| 파서 | eval 40 | eval_ext 56 | 합계 96 | 건당 |
|------|---------|-------------|---------|------|
| heuristic (키워드) | 35.0% | 42.9% | — | 0 s |
| **ollama gemma4:e4b (기본)** | 92.5% | **91.1%** (정규화 전 85.7%) | 88 | 5 s |
| LoRA `instance_v2` (배포 중) | 87.5% | 83.9% (정규화 전 80.4%) | 82 | 1~3 s |
| LoRA `instance_v3` (v2 + 승인 사용자 문장 8 ×3 + 증강 39) | 92.5% | 82.1% (정규화 전 78.6%) | 83 | 1~2 s |
| LoRA `instance_v3_nouser` (v3 에서 사용자 데이터만 뺌) | 92.5% | 80.4% (정규화 전) | — | 1 s |

정직한 해석:
- **사용자 문장 학습 효과는 아직 측정되지 않는다.** v3 와 사용자 데이터를 뺀 모델이 eval 40 에서 같고(92.5%),
  eval_ext 에서는 1문항 차이. v2 → v3 의 eval 40 상승(+5%p)은 재학습(누수 제거 포함) 차이였다.
  승인 문장이 8건뿐이라 당연한 결과 — 데이터가 수백 건 쌓인 뒤 다시 측정한다. 배포는 v2 유지
- **실제로 효과가 컸던 것은 어휘 정규화** (`prompt_spec.canonical_target` · `EFFECT_ALIASES`):
  Ollama 가 effect `"keep"` 을 내 해석 전체가 실패하던 3건(→ 키워드 파서로 떨어짐)과
  LoRA 의 `"flower pot"` · `"train car"` · `"pizza piece"` 같은 COCO 밖 이름을 바로잡아 **확장셋 +3.5~5.4%p**
- 남은 오답: LoRA 는 학습에 없는 대상(곰인형 → dog), "사람 지우고 배경만 남겨"(지움/남김 반전),
  "A 는 빼고 B 만 남겨"(target 이 A 로); Ollama 는 "크롭까지"(remove_bg+crop 을 crop 으로), 근거 없는 count 1

### 결과 (2026-09-30, `instance_v2`, RTX 4070 SUPER — Ollama 와 GPU 공유 상태)

| 파서 | 완전 일치 | target | effect | position | rank | count | attributes | 건당 |
|------|-----------|--------|--------|----------|------|-------|------------|------|
| heuristic (키워드) | 35.0% | 70.0% | 77.5% | 92.5% | 100% | 87.5% | 92.5% | 0 s |
| **ollama gemma4:e4b (기본)** | **92.5%** | 100% | 97.5% | 97.5% | 100% | 97.5% | 97.5% | 5.4 s |
| base Qwen2.5-1.5B (어댑터 없음) | 7.5% | 72.5% | 70.0% | 50.0% | 85.0% | 45.0% | 60.0% | 3.2 s |
| LoRA `instance_v1` (시드 600) | 77.5% | 97.5% | 87.5% | 100% | 100% | 97.5% | 90.0% | 1.2 s |
| **LoRA `instance_v2` (시드 800, 어휘 확장)** | **87.5%** | 95.0% | 97.5% | 100% | 100% | 100% | 92.5% | 1.8 s |

- LoRA 는 베이스 대비 7.5% → 87.5%. gemma 보다 5%p 낮고 약 3~5배 빠르다 (파이프라인 전체 2번째 요청부터 1.6 s)
- 남은 LoRA 오답: 문장 속 다른 명사에 끌림 ("말 사진에서 **사람** 지워" → horse,
  "가방 들고 있는 사람 말고 **가방**만" → person), "크롭까지" 해석
- 기본은 품질 우선으로 **Ollama 유지**, 속도가 필요하면 `LLM_PROVIDER=lora`
- 평가셋 문장은 학습에서 뺀다 (`train_lora.py --eval-file`, 기본 eval + eval_ext). v2 까지는 의사 라벨 32건이
  평가 문장 1개("사람만 남기고 배경 블러")와 같아 그 1문항이 누수였다 (2026-10-06 발견·수정)
- `--parsers ollama_rag` : 서비스와 같은 RAG 예시를 붙인 Ollama. 2026-10-04 기준 RAG 없음 95.0% (재측정),
  시드를 예시로 쓰면 90.0~92.5% 로 오히려 낮아 서비스 기본은 사용자 교정·좋아요만 사용
  → [`docs/guidance/llm-and-vision.md`](../../docs/guidance/llm-and-vision.md#프롬프트-해석-rag-사용자-교정-즉시-반영)

## 서빙

```env
LLM_PROVIDER=lora
LORA_BASE_MODEL=../training/models/qwen2.5-1.5b-instruct   # backend/ 기준
LORA_ADAPTER_PATH=models/lora                              # backend/models/lora
```

- `backend/app/services/prompt_lora.py` — transformers + peft 로 프로세스 안에서 추론
  (Ollama 는 Qwen2 safetensors 어댑터를 직접 붙이지 못함)
- 의존성·경로가 없거나 실패하면 휴리스틱으로 fallback
- 첫 요청에 모델 로드 (수 초), 이후 재사용

## 하지 않는 것

- YOLO-seg `best.pt` 학습 (→ `training/yolo/train_segment.py`)
- Ollama GGUF 직접 fine-tune, 허브 모델 자동 다운로드

## 관련

- `backend/app/services/prompt_spec.py`, `prompt_lora.py`, `instance_selector.py`
- `docs/plan/HARDCODING_ZONES.md`
- `scripts/fine_tune_lora.py` — 주간 배치 래퍼
