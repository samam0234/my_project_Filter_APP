# LLM · 비전 모델 실행 가이드

전략 본문: [`docs/plan/AI_MODEL_STRATEGY.md`](../plan/AI_MODEL_STRATEGY.md)

요청 한 건은 **LLM(문장 해석) → YOLO(대상 찾기) → 인스턴스 선택(규칙) → 효과**로 처리된다.

```text
"맨 앞 빨간 안전모 남자만 남기고 배경 제거"
   │ LLM (prompt_analyzer)
   ▼
{"target":["person"], "effect":"remove_bg",
 "selector":{"position":"front","count":1,"attributes":["red helmet"]}}
   │ YOLO26s-seg (segmentor) → person 인스턴스 6개
   │ instance_selector (규칙: 색 비율 · 위치 정렬 · 개수)
   ▼
맨 앞 1명 마스크 → effects (배경 투명)
```

---

## 비전: YOLO26s-seg (기본 스케일 s)

> 이전 문서의 YOLO26n 기본은 **s 로 통일**했다. 상세: [`docs/plan/YOLO26S_DEFAULT.md`](../plan/YOLO26S_DEFAULT.md)

서빙 가중치는 **`backend/models/`** (지금 서빙 중인 활성 모델), 원본·후보는 루트 `models/`.

```bash
# 학습 best.pt 또는 루트 보관본을 서빙 위치로 배포 + 샘플 추론
python training/yolo/apply_best.py
python training/yolo/apply_best.py --weights models/<후보>.pt --skip-predict

# ONNX export 예 (ultralytics 설치 환경)
# yolo export model=yolo26s-seg.pt format=onnx
```

`.env` (경로는 **backend/ 기준**):

```env
YOLO_MODEL_PATH=models/yolo26s-seg.pt   # → backend/models/yolo26s-seg.pt
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

## Fallback

- `LLM_PROVIDER=heuristic` 이거나, LLM 호출·파싱이 실패하면 `workflows/nodes.py` 키워드 파서 사용
- 키워드 파서도 지우기 동사·위치·서수·개수·색+부위를 인식한다 (평가 35%, 즉시 응답)
- 실제로 쓰인 파서는 결과 `meta.prompt_parser` 와 서버 로그 `prompt_analyzer … parser=` 로 확인
