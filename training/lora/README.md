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
data/feedback/*.json                       (사용자 like / dislike + 정답 JSON 코멘트)
data/pseudo_labels/*.json                  (단순 "X만 크롭" 계열 — 샘플링)
        ↓  dataset.py  (정답을 backend prompt_spec 으로 정규화 = 서빙과 같은 형식)
train_lora.py  --dry-run                   ← 레코드 수 확인
train_lora.py  --base-model …              → outputs/lora/<run>/adapter/
        ↓
eval_parser.py --adapter …                 ← seed/eval.jsonl 로 heuristic·ollama·base·lora 비교
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
| feedback `like` | 시스템 `parsed_prompt` | |
| feedback `dislike` | **코멘트가 ParsedPrompt JSON 일 때만** | 시스템 출력은 오답 |
| feedback `pipeline_failure` | 시스템 `parsed_prompt` (약한 정답) | `--skip-pipeline-failure` 로 제외 |
| `pseudo_labels` | `parsed_prompt` | `--max-pseudo 600` 샘플링 (selector 학습 희석 방지) |

- 문장에 숫자가 없으면 `intensity` 는 15 로 맞춘다 (의사 라벨의 "블러=20" 노이즈 제거)
- 응답 JSON 토큰에만 loss (지시문 암기 방지), 끝에 EOS
- `count` 규칙: 숫자 표현이나 위치 단어가 있을 때만. 명사만("남자") 으로는 채우지 않는다

### 사용자 피드백을 정답으로 넣는 법

dislike 코멘트에 올바른 JSON 을 적으면 다음 학습에 들어간다.

```json
{"target":["person"],"effect":"remove_bg","selector":{"position":"front","count":1,"attributes":["red helmet","neon yellow vest"]}}
```

## 실행

```powershell
# 저장소 루트, training venv
training\.venv\Scripts\Activate.ps1

python training/lora/seed/build_seed.py                # 시드 재생성 (선택)
python training/lora/train_lora.py --dry-run
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
- 평가셋 문장은 학습 시드에 들어가지 않는다 (생성 후 누수 검사)
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
