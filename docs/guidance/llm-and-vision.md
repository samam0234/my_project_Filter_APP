# LLM · 비전 모델 실행 가이드

전략 본문: [`docs/plan/AI_MODEL_STRATEGY.md`](../plan/AI_MODEL_STRATEGY.md)

요청 한 건은 **LLM(문장 해석) → YOLO(대상 찾기) → 인스턴스 선택(규칙) → 효과**로 처리된다.

```text
"맨 앞 빨간 안전모 남자만 남기고 배경 제거"
   │ LLM (prompt_analyzer)
   ▼
{"target":["person"], "effect":"remove_bg",
 "selector":{"position":"front","count":1,"attributes":["red helmet"]}}
   │ YOLO26m-seg (segmentor) → person 인스턴스 6개
   │ instance_selector (규칙: 색 비율 · 위치 정렬 · 개수)
   ▼
맨 앞 1명 마스크 → effects (배경 투명)
```

---

## 비전: YOLO26m-seg (기본 스케일 m)

> 이전 문서의 YOLO26n 기본은 **s 로 통일**했다. 상세: [`docs/plan/YOLO26S_DEFAULT.md`](../plan/YOLO26S_DEFAULT.md)

서빙 가중치는 **`backend/models/`** (지금 서빙 중인 활성 모델), 원본·후보는 루트 `models/`.

```bash
# 학습 best.pt 또는 루트 보관본을 서빙 위치로 배포 + 샘플 추론
python training/yolo/apply_best.py
python training/yolo/apply_best.py --weights models/<후보>.pt --skip-predict

# ONNX export 예 (ultralytics 설치 환경)
# yolo export model=yolo26m-seg.pt format=onnx
```

`.env` (경로는 **backend/ 기준**):

```env
YOLO_MODEL_PATH=models/yolo26m-seg.pt   # → backend/models/yolo26m-seg.pt
```

- 모델이 없거나 로드에 실패하면 중앙 타원 **stub 마스크**로 동작 (데모용)
- 요청 대상이 모델 라벨에 없으면 stub 이 아니라 **실패(failed)** + "감지된 대상: …" 안내
- 라벨 별칭: 프롬프트의 `handbag`·`backpack` ↔ 모델의 `bag` 등은 자동으로 맞춘다
  (`segmentation.LABEL_ALIASES`)

학습(세그 본선): [`training/README.md`](../../training/README.md)
· 학습 yaml 의 클래스 `names` 와 프롬프트 target 이 소문자로 같아야 한다.

Docker backend 의 Ollama 주소는 compose 가 `host.docker.internal:11434` 로 덮어쓸 수 있다
→ [`CURRENT_STACK.md`](../plan/CURRENT_STACK.md).

---

## 프롬프트 규격 (`ParsedPrompt`)

정본: `backend/app/services/prompt_spec.py` — 서비스 LLM 지시문과 LoRA 학습 레이블이 공유한다.

| 필드 | 값 | 의미 |
|------|-----|------|
| `target` | COCO 클래스 소문자 목록 | 대상 종류 (`person`, `dog`, `car` …) |
| `effect` | `remove_bg` · `blur` · `crop` · `none` | 선택한 대상을 **남기고** 나머지에 효과 |
|  | `remove_object` | 선택한 대상을 **지우고** 주변으로 메움 |
| `intensity` | 0~100 | 블러 강도 (문장에 숫자가 없으면 15) |
| `crop` | bool | 주 효과 뒤 추가 크롭 |
| `selector` | `null` 또는 아래 | `null` 이면 target 클래스 **전부** |

`selector`:

| 필드 | 값 | 예 |
|------|-----|-----|
| `position` | `front` `back` `left` `right` `center` `largest` `smallest` | "맨 앞", "왼쪽", "가장 큰" |
| `rank` | 1-based | "오른쪽에서 **두 번째**" → `right`, 2 |
| `count` | 정수 | 숫자 표현("두 명")이 있을 때만. 위치만 있으면 1 |
| `attributes` | `"색 부위"` 목록 | `"red helmet"`, `"neon yellow vest"`, `"white car"` |

인스턴스 선택 규칙과 튜닝값: `backend/app/services/instance_selector.py`
(색 HSV 범위, 부위별 세로 구간, front 점수 가중치 등 `【수동·튜닝】` 표시).

---

## 로컬 LLM: Ollama Gemma 4 E4B (기본)

```bash
ollama pull gemma4:e4b
ollama serve   # 기본 http://localhost:11434
```

`.env`:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
LLM_TIMEOUT_SECONDS=30   # 초과 시 휴리스틱으로 넘어감 (첫 호출은 모델 로드로 느림)
```

- 호출: `backend/app/services/prompt_llm.py` — Ollama native `/api/chat`, `format: json`, temperature 0
- 표준 라이브러리 `urllib` 만 사용 (Docker 경량 이미지 호환)
- 요청당 약 3~6 초

---

## 로컬 LoRA 어댑터 (선택: 빠른 파서)

`training/lora` 에서 학습한 Qwen2.5-1.5B 어댑터를 백엔드 프로세스 안에서 직접 돌린다.

```env
LLM_PROVIDER=lora
LORA_BASE_MODEL=../training/models/qwen2.5-1.5b-instruct   # backend/ 기준
LORA_ADAPTER_PATH=models/lora                              # backend/models/lora
```

- 필요 패키지: `transformers`, `peft` (+ torch) — 루트 `requirements.txt` 의 선택 줄
- 첫 요청에 모델 로드(수십 초), 이후 요청당 약 1~2 초
- 평가(2026-09-30, 40문항 완전 일치): **gemma4:e4b 92.5%** / **LoRA v2 87.5%** / 키워드 35%
  → 기본은 품질 우선으로 Ollama, 속도가 중요하면 lora
- 확장 평가(2026-10-06, 새 말투 56문항): gemma4 91.1% / LoRA v2 83.9% / 키워드 42.9% — 상세·사용자 문장 학습 결과는
  [`training/lora/README.md`](../../training/lora/README.md#확장-평가셋--사용자-문장-학습-2026-10-06)
- 학습·평가 방법: [`training/lora/README.md`](../../training/lora/README.md)

---

## 고도화 LLM

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```

### Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.0-flash
```

어느 provider 든 같은 `SYSTEM_PROMPT` 와 `normalize_parsed` 를 거쳐 같은 `ParsedPrompt` 가 나온다.

---

## 프롬프트 해석 RAG (사용자 교정 즉시 반영)

`backend/app/services/prompt_rag.py` — 지금 요청과 **비슷한 문장의 확인된 정답**을 찾아 `SYSTEM_PROMPT` 뒤에 예시로 붙인다.
사용자가 "정답 알려주기"로 교정하고 운영 콘솔에서 **승인하면**, LoRA 재학습 없이 다음 요청부터 반영된다.
ollama · openai · gemini 에만 적용 (lora 는 학습 템플릿이 고정이라 제외).

| 항목 | 내용 |
|------|------|
| 지식 베이스 | 학습 DB `learning_samples` 중 **승인된** 문장 — `correction`(사용자 교정) > `like` · `request`(회원 요청). 같은 문장이면 교정이 이김. 승인 전 교정은 쓰지 않음 ([`console-admin.md`](console-admin.md#학습-데이터-검수)) |
| 검색 | 글자 2·3-gram TF-IDF 코사인 (외부 모델·의존성 없음, 수천 건 규모 ms 단위) |
| 갱신 | 승인 샘플 수·최종 수정 시각이 바뀌면 `PROMPT_RAG_REFRESH_SECONDS`(30 s) 안에 자동 재색인. 학습 DB 가 없으면 예시 없이 진행 |
| 기록 | `meta.prompt_rag` 에 출처·점수만 (다른 사용자의 문장 원문은 남기지 않음) |

```env
PROMPT_RAG_ENABLED=true
PROMPT_RAG_SOURCES=correction,like,request   # seed 를 넣으면 PROMPT_RAG_SEED_FILE(기본 training/lora/seed/train.jsonl)도 사용 (비권장, 아래)
PROMPT_RAG_TOP_K=3
PROMPT_RAG_MIN_SCORE=0.6             # 같은 뜻의 다른 표현 0.62~0.73 / 틀만 같은 문장 0.3~0.46
```

평가 (2026-10-04, `seed/eval.jsonl` 40건, gemma4:e4b, 평가 문장과 같은 예시는 지식 베이스에서 제외):

| 구성 | 완전 일치 | 비고 |
|------|-----------|------|
| RAG 없음 | 95.0% | 기준 |
| 시드 800건 포함 (top 4, 0.2) | 90.0% | 표면만 비슷한 예시의 selector 를 따라감 (`count`·`position` 오답) |
| 시드 포함 + 지시 문구 보강 (top 3, 0.3) | 92.5% | 여전히 기준보다 낮음 → **시드는 기본 제외** |
| 교정·좋아요만 (현재 피드백, 0.6) | 92.5% | 예시가 붙은 문항은 1건이고 정답. 추가 오답 1건은 예시 없이 같은 요청 → Ollama 실행 간 흔들림 (±1건) |
| 교정·좋아요만 + 비슷한 표현 교정 2건 | **97.5%** | 기준의 오답 "앞줄 맨 앞 사람만 남기고 크롭까지" 가 교정 "앞줄 제일 앞 사람만 남기고 크롭해줘" 로 해결 |

- 교정이 없으면 예시가 붙지 않아 기준과 같은 동작 — RAG 가 해석을 망치지 않게 **임계값을 높게** 둔다
- 검색 버그 수정: 지식 베이스에 없는 n-gram 을 질의 벡터에서 빼면 "왼쪽 세 번째 자전거만 남기고 배경 제거" ↔
  "사람만 남기고 배경 제거" 가 0.88 로 떴다 → 가장 희귀한 IDF 로 남겨 0.40 으로 내려감
- 재현: `python training/lora/eval_parser.py --parsers ollama,ollama_rag` (`FEEDBACK_DIR`·`PROMPT_RAG_*` 환경변수로 구성 변경)

---

## LLM 이 꺼졌을 때의 키워드 파서 (폴백)

LLM 이 꺼져 있거나 실패하면 `workflows/nodes.parse_prompt_heuristic` 이 해석한다. 예전에는 대상을 5종만 알고 "X 말고 Y만"을 몰라
언급한 물체를 전부 대상으로 잡았다(대상 정확도 56.6%). 지금은 `services/heuristic_targets.py` 가 **어휘 확장(한·영·풍경) + 역할 규칙**으로 판정한다.

| 표현 | 역할 | 예 |
|------|------|-----|
| `Y만` · `Y 남기` · `keep Y` | 남길 대상 | "강아지만 남기고 사람은 지워줘" → dog |
| `X 말고/빼고/제외` · `X는 놔두고/그대로` · `ignore X` | 대상 아님 | "차는 빼고 사람만 남겨줘" → person |
| `Y 지워줘` · `Y만 지워줘` · `remove Y` | 지울 대상 (`remove_object`) | "자동차만 지워줘 사람은 건드리지 말고" → car |
| `A, B만` · `A랑 B만` · `keep A and B` | 이어진 언급은 같이 | "사람이랑 강아지만 남기고" → person, dog |
| 언급 없음 | 사람 | "배경 블러" → person |

한 글자 낱말 오탐을 막았다: "강도"의 강, "산책"의 산, "물건"의 물, "차이"의 차는 대상이 아니다.
평가: 4개 셋 183문장 대상 100% · 효과 96.2% (이전 56.6% · 85.3%). 규칙 완성 뒤 처음 본 홀드아웃 40문장은 97.5%(39/40)였다.
이 파서는 **LLM 답의 중재자**이기도 하다 — `PROMPT_CHAIN=langchain` 일 때 LLM 과 대상이 다르면 다수결에 한 표를 낸다.

## 어휘 정규화 (모든 파서 공통)

`prompt_spec.normalize_parsed` 가 LLM·LoRA 출력을 서비스 규격으로 맞춘다.

- target → **COCO 클래스 이름** (`canonical_target`): 별칭(`flower pot` → `potted plant`, `phone` → `cell phone`,
  한국어 `화분`·`곰인형`…) → 복수형 → 마지막 단어 순. 모르는 이름은 그대로 (세그에서 못 찾음)
- effect 별칭 (`EFFECT_ALIASES`): `keep`·`isolate`·`remove_background` → `remove_bg`, `erase`·`delete` → `remove_object` 등.
  그래도 모르는 값이면 기존처럼 실패 → 키워드 파서
- 이것만으로 확장 평가셋에서 Ollama 85.7% → 91.1%, LoRA v2 80.4% → 83.9%

## Fallback

- `LLM_PROVIDER=heuristic` 이거나, LLM 호출·파싱이 실패하면 `workflows/nodes.py` 키워드 파서 사용
- 키워드 파서도 지우기 동사·위치·서수·개수·색+부위를 인식한다 (평가 35%, 즉시 응답)
- 실제로 쓰인 파서는 결과 `meta.prompt_parser` 와 서버 로그 `prompt_analyzer … parser=` 로 확인
- RAG 검색이 실패해도 예시 없이 LLM 을 호출한다 (경고 로그 `프롬프트 RAG 검색 실패`)
