# 컷앤킵 (Cut & Keep) — 로직 구조

**한 줄 설명**  
프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

**근거 문서** (동일 폴더)
- `DEVELOPMENT_PLAN.docx` — 원본 상세 계획서
- `PROJECT_STRUCTURE.md` — 디렉토리·모듈 구조
- `DATABASE.md` — SQLite / MariaDB, ERD, Repository
- `AI_MODEL_STRATEGY.md` — YOLO26s-seg · Ollama E4B · OpenAI/Gemini
- `YOLO26S_DEFAULT.md` — 비전 기본 n→s 전환 안내
- `TESTING.md` — pytest 구조·실행 전 검증 전략
- `LOGIC_AND_GIT_BRANCH_STRATEGY.md` — 실행 규칙·브랜치
- `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md` — 환경·실행·배포



---

## 1. 시스템 목표와 범위

### 1.1 해결 문제
- AI 학습 데이터 준비 시 bbox 수작업의 비용·한계
- 사각형 라벨이 물체 실루엣을 반영하지 못하는 문제
- 복잡한 배경에서 특정 대상만 정밀 추출하기 어려움

### 1.2 제공 가치
- 자연어 프롬프트로 대상·효과(블러/크롭) 지정
- 픽셀 단위 세그멘테이션 마스크로 객체 추출
- 사용자 피드백 → Pseudo Labeling → LoRA 개선 루프

### 1.3 범위 (Phase 게이트)
| Phase | 범위 | 성공 기준(요약) |
|-------|------|-----------------|
| **P1 MVP** | 단일 이미지, **YOLO26s-seg**, Ollama E4B 프롬프트 분석, 피드백 UI | 기본 프롬프트 처리 데모 동작 |
| **P2** | Grounding DINO+SAM2, 배치 500장, LoRA | 배치 안정 완료 + 개선 루프 |
| **P3** | 영상 + Temporal Smoothing + 배포 | Docker 배포 가능한 완성 앱 |

**규칙**: Phase 1이 완전히 동작하기 전에 Phase 2+ 기능을 코드에 넣지 않는다.

---

## 2. 전체 아키텍처 (논리 계층)

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + TS + Zustand)                            │
│  Upload · Prompt · Before/After · Feedback · Batch UI       │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (multipart) / SSE·WS (P2)
┌───────────────────────────▼─────────────────────────────────┐
│  Router Layer  app/routers/                                 │
│  upload · feedback · jobs · batch · /health                 │
│  + schemas (Pydantic DTO)  · security (MIME/size)           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Workflow (LangGraph) + Services                            │
│  GraphState · nodes · image_processor · segment · effects   │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
┌───────────────▼───────────────┐   ┌─────────▼────────────────┐
│  Repository Layer             │   │  Files / Models          │
│  job / feedback / batch repo │   │  uploads · feedback · ONNX│
└───────────────┬───────────────┘   └──────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────────┐
│  ORM models + db/session                                      │
│  Local: SQLite (data/cutnkeep.db)  |  Prod: MariaDB           │
└───────────────────────────────────────────────────────────────┘
         P2: Celery+Redis  |  P3: Video + Optical Flow + LSTM
```

### 2.1 계층별 책임

| 계층 | 경로 | 책임 | 하지 않는 것 |
|------|------|------|--------------|
| **Frontend** | `frontend/` | UX, API 호출 | 모델 추론, DB 직접 접근 |
| **Router** | `app/routers/` | HTTP, Depends, 응답 매핑 | SQL, OpenCV 세부 |
| **Schema** | `app/schemas/` | 요청/응답 DTO | DB 테이블 정의 |
| **Workflow/Service** | `workflows/`, `services/` | 파이프라인·도메인 로직 | raw SQL |
| **Repository** | `app/repositories/` | CRUD / commit | 비즈니스 분기 |
| **Model (ORM)** | `app/models/` | 테이블 매핑 | HTTP |
| **DB** | `app/db/` | engine, session, init | 도메인 규칙 |

DB 상세·ERD: **`DATABASE.md`**


---

## 3. 핵심 처리 파이프라인 (7단계)

단일 요청(이미지 + 프롬프트)의 정본 흐름이다.  
구현 시 이 순서를 깨지 않는다.

```
[FE] 이미지 업로드 + 자연어 프롬프트
        │
        ▼
[1] FastAPI 수신 + 보안 검증
    · MIME / 확장자 / 크기(기본 ≤20MB)
    · 통과 실패 → 4xx, 파일 즉시 폐기
        │
        ▼
[2] Prompt Analyzer (LangGraph + LLM)
    · 자연어 → 구조화 JSON
    · 예: {"target":["dog"],"effect":"blur","intensity":15,"crop":false}
        │
        ▼
[3] OpenCV Preprocessing
    · imread, resize(종횡비 유지), CLAHE(clipLimit=2.0, tile=8×8)
    · 색공간 변환 · 모든 단계 .copy()로 원본 보존
        │
        ▼
[4] Segmentation
    · P1: **YOLO26s-seg** (.pt / ONNX)
    · P2: Grounding DINO + SAM2 (오픈보캐브 대상)
    · 프롬프트 분석 LLM: 기본 Ollama gemma4:e4b → 고도화 OpenAI/Gemini
      (docs/plan/AI_MODEL_STRATEGY.md)
        │
        ▼
[5] Mask Refinement + Effect
    · GrabCut + morphologyEx(MORPH_CLOSE)
    · GaussianBlur + bitwise_and (배경 블러)
    · boundingRect + crop / 알파 합성 / addWeighted
        │
        ▼
[6] Validator
    · 마스크 면적·confidence 품질 체크
    · 실패 시 fallback (재시도 또는 안전 결과)
        │
        ▼
[7] 응답 + Feedback Loop
    · Before/After 반환
    · 싫어요/실패 → data/feedback/ (image + JSON)
    · P2: Pseudo Label → 주 1회 LoRA (오프라인)
```

### 3.1 단계 ↔ 코드 매핑 (구현 앵커)

| Step | 모듈 (예정) | Feature 브랜치 |
|------|-------------|----------------|
| 1 | `api/endpoints/upload.py`, `core/security.py` | `feature/backend` |
| 2 | `workflows/nodes.py` (`prompt_analyzer`) | `feature/llm`, `feature/langgraph` |
| 3 | `services/image_processor.py` | `feature/opencv` |
| 4 | `services/segmentation.py` | `feature/yolo` → `feature/sam2` |
| 5 | `services/effects.py` | `feature/opencv` |
| 6 | `services/validator.py` | `feature/langgraph` |
| 7 | `services/feedback_service.py`, `api/.../feedback.py` | `feature/feedback` |

---

## 4. LangGraph 워크플로우 로직

### 4.1 GraphState (공유 상태)

```text
GraphState
├── image_bytes / image_path     # 입력
├── original_image               # 원본 ndarray 보존본
├── prompt: str                  # 사용자 자연어
├── parsed_prompt: dict          # target, effect, intensity, crop, ...
├── preprocessed_image
├── mask
├── confidence / quality_score
├── effect_result
├── result_image                 # 최종 출력
├── status: pending|ok|fallback|failed
├── error: str | null
└── feedback_meta                # 실패 시 저장용
```

### 4.2 노드

| 노드 | 입력 | 출력 | 기술 |
|------|------|------|------|
| `prompt_analyzer` | prompt | parsed_prompt | LangChain + LLM |
| `preprocessor` | image | preprocessed_image | OpenCV |
| `segmentor` | preprocessed + target | mask, confidence | YOLO / DINO+SAM2 |
| `effect_applier` | image + mask + effect | effect_result | OpenCV |
| `validator` | mask + scores | status, result or fallback | 커스텀 규칙 |
| `feedback_collector` | failed case | disk write | FS + JSON |

### 4.3 엣지(조건부 분기)

```
START
  → prompt_analyzer
  → preprocessor
  → segmentor
  → validator ──(quality OK)──→ effect_applier → END
              └──(quality NG)──→ fallback / retry segmentor
                                 └──(still fail)→ feedback_collector → END
effect_applier:
  · parsed_prompt.effect == blur  → blur path
  · parsed_prompt.crop == true    → crop path
  · 둘 다 / 배경 제거만           → mask composite path
```

**원칙**
- 오케스트레이션은 graph에, 연산은 services에 둔다.
- 노드는 순수하게 state in → state out (부작용은 feedback/storage 노드에 한정).

---

## 5. 서비스 로직 상세

### 5.1 image_processor (파이프라인 조립)
- 7단계 중 OpenCV 구간(3, 5)을 순차 호출하는 facade
- 단일이미지 동기 경로의 기본 엔트리
- 배치(P2)에서는 generator로 한 장씩 호출

### 5.2 segmentation
```
P1: load ONNX YOLO-seg → predict → instance masks → target 필터
P2: text prompt → Grounding DINO boxes → SAM2 masks
공통 출력: binary/soft mask + confidence list
```

### 5.3 effects
| effect | 연산 |
|--------|------|
| remove_bg | mask 알파 합성 / 투명 배경 |
| blur | 배경 GaussianBlur + bitwise 합성 |
| crop | mask boundingRect + 여백 옵션 |

### 5.4 validator
- 마스크 면적 비율 하한/상한
- confidence 임계값
- 빈 마스크 / 전역 마스크 거부
- fallback: 임계 완화 재시도 → 실패 시 원본+에러 메타 + feedback 큐

### 5.5 feedback_service
- 저장: `data/feedback/{id}.jpg` + `{id}.json`
- JSON: prompt, parsed, model_version, scores, user_vote, timestamp
- P2: Pseudo Labeling 입력으로 사용 → LoRA 학습 스크립트 연동

---

## 6. API · 데이터 계약 (논리)

### 6.1 엔드포인트

| Method | Path | Phase | 설명 |
|--------|------|-------|------|
| POST | `/api/v1/upload` | P1 | 단일 이미지 + prompt → 결과 (**DB jobs 저장**) |
| GET | `/api/v1/jobs/{job_id}` | P1 | DB에서 job 조회 |
| GET | `/api/v1/jobs` | P1 | 최근 job 목록 |
| POST | `/api/v1/feedback` | P1 | like/dislike → **DB feedbacks** + 파일 사이드카 |
| GET | `/health` | P1 | 헬스체크 (+ `db_dialect`) |
| POST | `/api/v1/batch` | P2 | 다중 업로드 → job_id (**batch_jobs**) |
| GET | `/api/v1/batch/{job_id}` | P2 | 진행률·결과 |
| WS/SSE | `/api/v1/batch/{job_id}/stream` | P2 | 실시간 진행률 |


### 6.2 업로드 요청/응답 (개념)

**Request**
- `file`: image/jpeg|png|webp
- `prompt`: string

**Response (success)**
```json
{
  "job_id": "uuid",
  "parsed_prompt": { "target": ["dog"], "effect": "blur", "intensity": 15, "crop": false },
  "before_url": "...",
  "after_url": "...",
  "quality_score": 0.91,
  "status": "ok"
}
```

**Response (fallback/failed)**
```json
{
  "job_id": "uuid",
  "status": "fallback" | "failed",
  "message": "...",
  "feedback_saved": true
}
```

### 6.3 보안·수명 규칙
- MIME + 확장자 + 크기 검증 필수
- 일반 업로드: **24시간 후 자동 삭제** (임시 파일은 즉시 삭제)
- **영구 보관 금지** (예외: feedback 실패 케이스만)

---

## 7. Frontend 로직

```
App
├── ImageUploader          → 파일 선택/드롭
├── PromptInput            → 자연어 입력
├── ProcessingStatus       → 로딩/에러
├── BeforeAfterViewer      → 결과 비교
├── FeedbackButtons        → like/dislike → /feedback
└── BatchUploader (P2)     → 다중 업로드 + progress
```

**상태 (Zustand 개념)**
```text
useAppStore
├── file / previewUrl
├── prompt
├── isProcessing
├── result { before, after, jobId, status }
├── error
└── actions: setFile, setPrompt, process, sendFeedback, reset
```

**훅**
- `useImageProcessing` — upload API 호출·에러 처리
- `useFeedback` — 피드백 POST

---

## 8. 배치·영상 확장 로직

### 8.1 배치 (Phase 2)
```
POST /batch → Celery task enqueue
  worker: for image in generator(files):
            run same 7-step pipeline
            update Redis progress
  client: poll or SSE → progress %
```
- 최대 500장
- 메모리: **반드시 generator/스트리밍** (한 번에 전체 로드 금지)

### 8.2 영상 (Phase 3)
```
video → frames
  per frame: 7-step pipeline
  Temporal Smoothing: Optical Flow + LSTM/GRU
  → reassembled video
```
- 목표: 프레임 간 마스크 깜빡임/흔들림 감소

---

## 9. 피드백 → 학습 루프 (Phase 2)

```
User dislike / validator fail
        │
        ▼
data/feedback/ (image + meta JSON)
        │
        ▼
Pseudo Labeling (Grounding DINO + SAM2)
        │
        ▼
주 1회 오프라인 LoRA Fine-tune (Colab 스크립트)
        │
        ▼
LoRA 가중치만 서버 교체 (전체 재배포 최소화)
```

**원칙**: 완전 자동 무한 학습이 아니라 **가벼운 반자동 개선**.

---

## 10. 모듈 의존성 (허용 방향)

```
api  → workflows → services → utils / models(onnx)
api  → core (config, security)
services ↛ api          (순환 금지)
workflows ↛ api
frontend ↛ backend 내부 모듈 (HTTP만)
```

설정·경로·모델명은 **`core/config.py` (Pydantic Settings)** 단일 출처.

---

## 11. Phase 1 구현 순서 (로직 기준)

1. **OpenCV 파이프라인** — preprocess + mask refine + effects (단위 테스트 가능)
2. **YOLO-seg ONNX** — segmentor 교체 가능한 인터페이스
3. **LangGraph 골격** — state + linear path + validator stub
4. **FastAPI upload + security**
5. **React 업로드/결과/피드백**
6. **feedback 저장 경로 연결**

이후 Phase 2에서 segmentor 백엔드 교체·배치·LoRA만 확장.

---

## 12. 불변 실행 규칙 (로직 가드)

1. Phase 단위 확장 — 미완성 Phase에 다음 기능 혼입 금지  
2. OpenCV 전 단계 `.copy()` 원본 보존  
3. 배치 = Generator  
4. 실패 = `data/feedback/` 자동 저장  
5. 하드코딩 경로 금지 → config  
6. Phase 1 모델 = YOLO-seg + ONNX만  
7. 업로드 비영구 · feedback만 예외 보관  

---

## 13. docs/plan 문서 맵

| 파일 | 역할 |
|------|------|
| **`LOGIC_STRUCTURE.md`** (본 문서) | 통합 로직 구조 — 구현 시 1순위 참조 |
| **`DATABASE.md`** | SQLite/MariaDB, ERD, Repository, 환경변수 |
| `DEVELOPMENT_PLAN.docx` | 원본 상세 계획서 (Why/Phase/일정) |
| `PROJECT_STRUCTURE.md` | 폴더·파일 트리 |
| `LOGIC_AND_GIT_BRANCH_STRATEGY.md` | 실행 규칙 + Git 전략 |
| `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md` | 환경 세팅·로컬 실행·Docker |


---

**다음 구현 진입점 추천**  
`backend/app/services/image_processor.py` + `workflows/` skeleton → `feature/opencv` / `feature/yolo`
