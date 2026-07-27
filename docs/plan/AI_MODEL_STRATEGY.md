# 컷앤킵 — AI 모델 전략 (YOLO26n-seg + Ollama E4B + 클라우드 LLM)

**상태:** Phase 1 확정 방향 (2026-07 기준)  
**관련:** `LOGIC_STRUCTURE.md`, `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`, `.env.example`, `RUN.md`

---

## 1. 판단 요약

| 선택 | 판정 | 한 줄 |
|------|------|--------|
| **YOLO26n-seg** (세그멘테이션) | **좋음** | 최신 nano 급으로 로컬·Docker 적합, 인스턴스 마스크 확보 |
| **Ollama `gemma4:e4b` (E4B)** 로컬 LLM | **좋음 (기본)** | 키 없이 프롬프트 구조화, 프라이버시·비용 0 |
| **고도화: OpenAI API** | **좋음 (품질 축)** | 복잡한 한국어 프롬프트·안정 JSON에 유리 |
| **고도화: Gemini API** | **좋음 (비용·쿼터 축)** | 무료/저비용 구간이 넓을 때 실사용 트래픽용 |

**종합:**  
「로컬은 가벼운 비전(YOLO26n-seg) + 가벼운 LLM(Ollama E4B), 고도화는 LLM만 클라우드로 갈아끼우기」는  
컷앤킵 1인 개발·Phase 게이트와 **잘 맞는 판단**이다.  
세그 품질이 부족할 때만 Phase 2에서 SAM2 등으로 비전 축을 올리면 된다.

---

## 2. 비전: YOLO26n-seg

### 2.1 왜 n(나노) + seg 인가

- **세그멘테이션(`-seg`)**: bbox만 있는 detect 모델이 아니라 **픽셀 마스크**가 나와 배경 제거/블러 전제와 맞음.
- **YOLO26 계열**: Ultralytics 최신 라인. 인스턴스 세그에서 이전 세대 대비 마스크 품질·속도 개선 보고.
- **n 스케일**: CPU/노트북·Docker slim 이미지에서 현실적인 추론 속도. Phase 1 MVP 검증에 적합.
- 필요 시 같은 파이프라인으로 `yolo26s-seg` / `m` 등으로 **파일 경로만 교체** 가능.

### 2.2 권장 산출물

| 용도 | 파일 예 |
|------|---------|
| 학습/로컬 Ultralytics | `models/yolo26n-seg.pt` |
| 배포·ONNX Runtime | `models/yolo26n-seg.onnx` |

```bash
# 예시 (ultralytics CLI / Python export)
# yolo export model=yolo26n-seg.pt format=onnx
```

### 2.3 주의

- Docker 경량 이미지(`requirements.docker.txt`)에는 기본적으로 **torch/ultralytics 없음** →  
  개발 머신에서 가중치·ONNX를 만들고 `models/`에 두거나, 풀 `requirements.txt` 환경에서 추론.
- COCO 클래스 밖 대상은 Phase 1에서 약함 → 계획서대로 Phase 2 **Grounding DINO + SAM2** 또는 피드백 LoRA.

### 2.4 환경변수

```env
YOLO_MODEL_PATH=models/yolo26n-seg.pt
# 또는
# YOLO_MODEL_PATH=models/yolo26n-seg.onnx
```

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
**세그=YOLO26n-seg, 프롬프트 파싱=E4B** 가 Phase 1에 더 안정적이다.  
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
Phase 1 개발:  LLM_PROVIDER=ollama  (gemma4:e4b)
데모 고품질:   LLM_PROVIDER=openai  (OPENAI_API_KEY)
비용 실험:    LLM_PROVIDER=gemini  (GEMINI_API_KEY)
실패 시:      heuristic 파서 fallback (현재 nodes.parse_prompt_heuristic)
```

**비전(세그)은 당분간 YOLO26n-seg 고정.** LLM 클라우드 전환과 분리할 것.

---

## 5. 아키텍처 권장 (프로바이더 추상화)

```
prompt_analyzer 노드
        │
        ▼
  LLMClient 인터페이스
   ├─ OllamaClient   (기본, OpenAI-compat or native)
   ├─ OpenAIClient
   └─ GeminiClient
        │
        ▼
  ParsedPrompt JSON  (schemas.request.ParsedPrompt)
        │
        ▼
  segmentor (YOLO26n-seg) → effects → validator
```

- 설정은 `core/config.py` + `.env` 만 변경
- 키가 없거나 Ollama down 이면 **휴리스틱 파서로 fallback** (이미 skeleton 존재)

---

## 6. Phase와 모델 매핑

| Phase | 비전 | LLM |
|-------|------|-----|
| **P1** | YOLO26n-seg (ONNX 권장 배포) | Ollama E4B 기본 |
| **P1 데모 강화** | 동일 | OpenAI 또는 Gemini 스위치 |
| **P2** | + Grounding DINO / SAM2, 배치 | 클라우드 LLM + 로컬 fallback 유지 |
| **P3** | 영상 + temporal | 동일 LLM 계층 재사용 |

---

## 7. 리스크 · 완화

| 리스크 | 완화 |
|--------|------|
| E4B 비전 불안정 | Phase 1 LLM은 텍스트 JSON만; 비전은 YOLO |
| YOLO n 정확도 한계 | s/m 모델 경로 교체, Phase 2 SAM2 |
| Ollama 미기동 | heuristic fallback + `/health` 에 llm 상태 표시(추후) |
| API 비용 | 기본 ollama, 클라우드 키는 선택 env |
| Docker 이미지 비대화 | 추론 이미지와 학습/export 환경 분리 (현 requirements.docker.txt 방향 유지) |

---

## 8. 체크리스트 (도입 시)

- [ ] `ollama pull gemma4:e4b` 후 로컬 응답 확인  
- [ ] `yolo26n-seg.pt` 다운로드 또는 학습 산출물 배치  
- [ ] (선택) ONNX export → `YOLO_MODEL_PATH`  
- [ ] `.env` 에 `LLM_PROVIDER=ollama` 설정  
- [ ] 프롬프트 1건 → ParsedPrompt JSON 단위 테스트  
- [ ] 업로드 1건 → 마스크·효과 e2e  
- [ ] (고도화) OpenAI/Gemini 키로 provider 전환 스모크  

---

## 9. 관련 경로

| 경로 | 내용 |
|------|------|
| **`training/`** | **학습 전용 구역** (yolo detect/seg, lora, datasets, outputs) |
| `training/yolo/train_segment.py` | 세그 학습 진입점 |
| `training/yolo/train_detect.py` | 탐지 학습 진입점 |
| `training/lora/train_lora.py` | LoRA 스캐폴드 (Phase 2) |
| `.env.example` | YOLO / LLM 환경변수 템플릿 |
| `backend/app/core/config.py` | Settings |
| `backend/app/services/segmentation.py` | 추론 시 YOLO 로드 |
| `docs/guidance/llm-and-vision.md` | 실행 가이드 (요약) |
| `RUN.md` | Ollama·모델 기동 메모 |

---

**결론:**  
YOLO26n-seg + Ollama E4B 기본, OpenAI/Gemini를 고도화 스위치로 두는 구성은 **추천한다.**  
문서·env 가이드를 이 전략에 맞춰 동기화한다.
