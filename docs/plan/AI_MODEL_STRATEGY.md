# 컷앤킵 — AI 모델 전략 (YOLO26m-seg + Ollama E4B + 클라우드 LLM)

**상태:** Phase 1 확정 방향 (비전 기본 **YOLO26m-seg**, 2026-10-06 s→m)  
**관련:** `LOGIC_STRUCTURE.md`, `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`, `.env.example`, `RUN.md`  
**변경 메모:** `docs/plan/YOLO26S_DEFAULT.md` (n → s), `docs/plan/YOLO26M_DEFAULT.md` (s → m)

---

## 1. 판단 요약

| 선택 | 판정 | 한 줄 |
|------|------|--------|
| **YOLO26m-seg** (세그멘테이션) | **좋음 (기본)** | medium 급 — COCO val2017 실험에서 s 보다 검출률·선택 정확도 높음 (2026-10-06) |
| **YOLO26s** (detection) | **좋음 (학습·실험)** | bbox 탐지 학습/검수. 서비스 마스크 본선은 아님 |
| **Ollama `gemma4:e4b` (E4B)** 로컬 LLM | **좋음 (기본)** | 키 없이 프롬프트 구조화, 프라이버시·비용 0 |
| **고도화: OpenAI API** | **좋음 (품질 축)** | 복잡한 한국어 프롬프트·안정 JSON에 유리 |
| **고도화: Gemini API** | **좋음 (비용·쿼터 축)** | 무료/저비용 구간이 넓을 때 실사용 트래픽용 |

**종합:**  
「로컬 비전은 **YOLO26m-seg** + 가벼운 LLM(Ollama E4B), 고도화는 LLM만 클라우드」가  
컷앤킵 Phase 1 기본이다. (n → s → **m**. 검출 비교는 `YOLO26M_DEFAULT.md`.)  
더 가볍게 되돌리려면 `YOLO_MODEL_PATH=models/yolo26s-seg.pt` 처럼 **경로만 교체**한다.

---

## 2. 비전: YOLO26m-seg

### 2.1 왜 m(medium) + seg 인가

- **세그멘테이션(`-seg`)**: bbox만 있는 detect 모델이 아니라 **픽셀 마스크**가 나와 배경 제거/블러 전제와 맞음.
- **YOLO26 계열**: Ultralytics 최신 라인. 인스턴스 세그 마스크 품질·속도 개선.
- **m 스케일 (서빙 기본, 2026-10-06)**: COCO val2017 비교에서 직접 학습 s(5클래스)와 COCO s 보다 검출률·선택 정확도가 높고, l 과의 차이는 작다. 근거는 `YOLO26M_DEFAULT.md`.
- **detect (`yolo26s.pt`)**: 학습 구역·검수용. 서비스 `Segmentor` 는 **seg 가중치** 전제.
- 학습 스크립트 출발 가중치(`train_segment.py` 기본 `yolo26s-seg.pt`)는 서빙 기본과 별개다.

### 2.2 권장 산출물

| 용도 | 파일 예 |
|------|---------|
| **서빙 (백엔드가 로드)** | `backend/models/yolo26m-seg.pt` (`apply_best.py` 로 배포) |
| 원본·후보 보관 | `models/yolo26m-seg.pt`, `models/yolo26s.pt` (detect 실험용) |
| 배포·ONNX Runtime | `backend/models/yolo26m-seg.onnx` (`SEG_RUNTIME=onnx`, `onnx_utils.py`. `docs/plan/ONNX_INFERENCE.md`) |

```bash
# 예시 (ultralytics CLI / Python export)
# yolo export model=yolo26m-seg.pt format=onnx
```

### 2.3 주의

- Docker 경량 이미지(루트 `requirements.docker.txt`)에는 기본적으로 **torch/ultralytics 없음** →  
  개발 머신에서 가중치·ONNX를 만들고 `backend/models/`에 두거나, 루트 풀 `requirements.txt` 환경에서 추론.
- COCO 클래스 밖 대상은 Phase 1에서 약함 → 계획서대로 Phase 2 **Grounding DINO + SAM2** 또는 피드백 LoRA.
- **detect 전용 `.pt` 를 YOLO_MODEL_PATH 에 넣지 말 것** — masks 없어 stub 로 떨어질 수 있음.

### 2.4 환경변수

```env
YOLO_MODEL_PATH=models/yolo26m-seg.pt      # backend/ 기준 → backend/models/
# 또는
# YOLO_MODEL_PATH=models/yolo26m-seg.onnx
```

- 현재 서빙 가중치는 **5클래스 커스텀**(person·dog·cat·car·bag). COCO 이름(`handbag` 등)은
  `segmentation.LABEL_ALIASES` 로 맞추지만, 버스·노트북 등 모르는 클래스는 "대상 없음"이 된다.

---

## 3. LLM: 로컬 Ollama E4B (기본)

### 3.1 모델 지정

Ollama 라이브러리 기준 **Gemma 4 Effective 4B**:

```bash
ollama pull gemma4:e4b
ollama run gemma4:e4b
```

- 역할: 자연어 프롬프트 → JSON (`target`, `effect`, `intensity`, `crop` 등)
- API: OpenAI 호환 엔드포인트 `http://localhost:11434/v1` (또는 Ollama native)

### 3.2 왜 좋은가

- **비용 0 / 오프라인 / 키 불필요** → 로컬 개발 마찰 최소
- 프롬프트 분석은 **짧은 JSON 구조화**라 4B급으로 충분한 경우가 많음
- 서버 코드는 `LLM_PROVIDER=ollama` 한 줄로 두고, 나중에 openai/gemini 로만 바꾸면 됨

### 3.3 이미지(멀티모달)에 대해

사용자 목표: “이미지라도 로컬에서 돌리기”.

| 점 | 내용 |
|----|------|
| Gemma 4 E4B 계열 | 설계상 멀티모달(텍스트+이미지 등)을 표방하는 변형이 있음 |
| Ollama 실제 지원 | **시점·빌드에 따라 비전 입력이 불완전하거나 텍스트 전용으로 동작하는 사례**가 보고됨 |
| 컷앤킵 Phase 1 권장 | **텍스트 프롬프트 구조화는 E4B**, 마스크는 **YOLO-seg** 가 주력 |
| 로컬 비전 LLM이 꼭 필요하면 | Ollama에서 비전 검증된 모델(예: `llava`, `llama3.2-vision` 등)을 **별 프로파일**로 두고 E4B와 분리 |

즉, “이미지 이해까지 전부 E4B”에 올인하기보다  
**세그=YOLO26m-seg, 프롬프트 파싱=E4B** 가 Phase 1에 더 안정적이다.  
이미지 조건 프롬프트(“이 사진 속 빨간 가방만”)는 Phase 2 오픈보캐브/비전 LLM과 맞물리는 편이 안전.

### 3.4 환경변수 (로컬 기본)

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
# OpenAI 호환 호출 시
# LLM_BASE_URL=http://localhost:11434/v1
```

---

## 4. 고도화: OpenAI vs Gemini

둘 다 “좋은 선택”이지만 **역할이 다름**. 배타 선택이 아니라 **프로바이더 스위치**로 두는 것을 권장.

### 4.1 OpenAI API

| 장점 | 단점 |
|------|------|
| JSON 모드·도구 호출 성숙, 한국어 지시 안정성 | 유료, 키·쿼터 관리, 데이터 외부 전송 |
| 문서·SDK 풍부, LangChain 연동 쉬움 | 로컬 오프라인 불가 |

**언제:** 데모/포트폴리오 품질, 애매한 자연어(“조금 더 타이트하게 크롭”) 처리, 운영 안정성 우선.

### 4.2 Gemini API

| 장점 | 단점 |
|------|------|
| 무료·저비용 구간이 넓어 **실험·트래픽 여유**에 유리 | 요금제·쿼터·지역 정책 변동 |
| 멀티모달 강점 (이미지+텍스트) 활용 여지 | 응답 형식·레이트리밋 대응 필요 |

**언제:** 비용 민감, 대량 프롬프트 실험, 이미지+프롬프트 동시 이해 실험.

### 4.3 권장 단계

```text
Phase 1 개발:  LLM_PROVIDER=ollama  (gemma4:e4b)          ← 기본, 평가 92.5%
빠른 로컬:     LLM_PROVIDER=lora    (Qwen2.5-1.5B + LoRA) ← 2026-10-09 조합형 재학습 후 283문장 94.7% (Ollama 체인 85.2%), GPU 문장당 약 1 s — GPU 서버 기본 (docker-compose.gpu.yml)
데모 고품질:   LLM_PROVIDER=openai  (OPENAI_API_KEY)
비용 실험:    LLM_PROVIDER=gemini  (GEMINI_API_KEY)
실패 시:      heuristic 파서 fallback (nodes.parse_prompt_heuristic, 평가 35%)
```

평가: `training/lora/eval_parser.py` · 손으로 쓴 40문항 (`training/lora/seed/eval.jsonl`) 완전 일치 기준.

**비전(세그)은 당분간 YOLO26m-seg 고정.** LLM 클라우드 전환과 분리할 것.

---

## 5. 아키텍처 권장 (프로바이더 추상화)

```
prompt_analyzer 노드 (workflows/nodes.py)
        │
        ▼
  services/prompt_llm.parse_prompt_llm  ← LLM_PROVIDER 분기
   ├─ ollama  : /api/chat (urllib, format=json)
   ├─ openai  : chat/completions (json_object)
   ├─ gemini  : generateContent (application/json)
   └─ lora    : services/prompt_lora (transformers + peft, 프로세스 내)
        │  지시문·정규화: services/prompt_spec (SYSTEM_PROMPT · LORA_TEMPLATE · normalize_parsed)
        ▼
  ParsedPrompt JSON  (target · effect · intensity · crop · selector)
        │
        ▼
  segmentor (YOLO26m-seg) → instance_selector (위치·순서·개수·색) → validator → effects
```

- 설정은 `core/config.py` + `.env` 만 변경
- 키가 없거나 호출이 실패하면 `LLM_FALLBACK`(기본 ollama)을 한 번 더 시도하고, 그것도 실패하면 **휴리스틱**
- "특정 인스턴스"를 고르는 것은 LLM 이 아니라 규칙(`instance_selector`) — LLM 은 조건만 뽑는다

---

## 6. Phase와 모델 매핑

| Phase | 비전 | LLM |
|-------|------|-----|
| **P1** | YOLO26m-seg (ONNX 권장 배포) + 규칙 기반 인스턴스 선택 | Ollama E4B 기본 · LoRA 선택 |
| **P1 데모 강화** | 동일 | OpenAI 또는 Gemini 스위치 |
| **P2** | Grounding DINO / SAM2 (`OPEN_VOCAB_ENABLED`, 로컬 가중치), 배치(기본 인프로세스, Celery 는 선택) | 클라우드 LLM + `LLM_FALLBACK` |
| **P3** | 영상 프레임 세그 + 직전 마스크 유지 (avi). 광학 흐름은 후속 | 동일 LLM 계층 재사용 |

---

## 7. 리스크 · 완화

| 리스크 | 완화 |
|--------|------|
| E4B 비전 불안정 | Phase 1 LLM은 텍스트 JSON만; 비전은 YOLO |
| YOLO s 정확도·속도 한계 | n(경량) 또는 m(품질) 경로 교체, Phase 2 SAM2 |
| Ollama 미기동 | heuristic fallback + `/health` 에 llm 상태 표시(추후) |
| API 비용 | 기본 ollama, 클라우드 키는 선택 env |
| Docker 이미지 비대화 | 추론 이미지와 학습/export 환경 분리 (현 requirements.docker.txt 방향 유지) |

---

## 8. 체크리스트 (도입 시)

- [x] `ollama pull gemma4:e4b` 후 로컬 응답 확인  
- [x] `yolo26m-seg.pt` 학습 산출물 배치 (`backend/models/`)  
- [x] (선택) ONNX 추론 (`onnx_utils.py`, `SEG_RUNTIME=onnx`)  
- [x] `.env` 에 `LLM_PROVIDER=ollama` 설정  
- [x] 프롬프트 → ParsedPrompt 단위 테스트 + 평가 (`training/lora/eval_parser.py`)  
- [x] 업로드 1건 → 마스크·효과 e2e (인스턴스 선택·지우기 포함)
- [x] LoRA 어댑터 학습·서빙 (`LLM_PROVIDER=lora`)  
- [ ] (고도화) OpenAI/Gemini 키로 provider 전환 스모크  

---

## 9. 관련 경로

| 경로 | 내용 |
|------|------|
| **`training/`** | **학습 전용 구역** (yolo detect/seg, lora, datasets, outputs) |
| `training/yolo/train_segment.py` | 세그 학습 진입점 (기본 `yolo26s-seg.pt` — 서빙 기본 m 과 별개, 직접 학습용) |
| `training/yolo/train_detect.py` | 탐지 학습 진입점 (기본 `yolo26s.pt`) |
| `training/lora/train_lora.py` | 시드·피드백·의사라벨 → 프롬프트 분석 LoRA |
| `training/lora/eval_parser.py` | heuristic · ollama · base · lora 비교 평가 |
| `backend/app/services/prompt_spec.py` | 프롬프트 규격 정본 (서빙·학습 공용) |
| `backend/app/services/instance_selector.py` | 특정 인스턴스 선택 규칙 |
| `.env.example` | YOLO / LLM 환경변수 템플릿 |
| `backend/app/core/config.py` | Settings (`YOLO_MODEL_PATH` 기본 `models/yolo26m-seg.pt`) |
| `backend/app/services/segmentation.py` | 추론 시 YOLO 로드 |
| `docs/guidance/llm-and-vision.md` | 실행 가이드 (요약) |
| `docs/plan/YOLO26S_DEFAULT.md` | n→s 전환 안내 |
| `docs/plan/YOLO26M_DEFAULT.md` | s→m 전환 (현재 서빙 기본) |
| `docs/plan/ONNX_INFERENCE.md` | torch 없는 ONNX 세그 추론 |
| `RUN.md` | Ollama·모델 기동 메모 |

---

**결론:**  
**YOLO26m-seg** + Ollama E4B 기본, OpenAI/Gemini를 고도화 스위치로 두는 구성은 **추천한다.**  
서빙·env 기본은 **m**. 학습 스크립트의 출발 가중치만 s-seg 를 유지한다 (직접 학습용).
