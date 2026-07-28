# 컷앤킵 (Cut & Keep) - 프로젝트 구조 기획서

**프로젝트명**: 컷앤킵 (Cut & Keep)  
**영문 표기**: Cut & Keep  
**한 줄 설명**: 프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱  
**개발 스타일**: 1인 개발, 모듈러 & 확장성 중심, Phase별 점진적 개발  
**관련 문서**: `LOGIC_AND_GIT_BRANCH_STRATEGY.md` (로직 + 실행 규칙 + Git 전략)

---

## 1. 전체 디렉토리 구조

```bash
cut-and-keep/
├── backend/                          # FastAPI 백엔드 (Python)
├── frontend/                         # React 사용자 앱 (:5173)
├── console/                          # React 운영 관리자 콘솔 (:5174)
├── scripts/                          # 운영 유틸 (cleanup 등)
├── training/                         # YOLO detect/seg · LoRA 학습 구역
├── tests/                            # pytest 실행 전 검증 (unit/structure/smoke)
├── models/                           # 추론용 가중치 (ONNX, pt)
├── data/                             # 데이터셋 & 피드백 데이터
├── docker/                           # Docker 관련 설정
├── docs/                             # 문서 허브 (Architecture, branchs, guidance, …)
├── logs/                             # 런타임 로그
├── requirements.txt                  # Python 로컬 개발 의존성 (루트)
├── requirements.docker.txt           # Docker 경량 런타임 의존성 (루트)
├── .env
├── docker-compose.yml
└── README.md
```


---

## 2. 상세 폴더 구조

### 2.1 backend/ (FastAPI)

```bash
backend/
├── app/
│   ├── main.py                      # FastAPI 진입점, lifespan, middleware
│   ├── core/
│   │   ├── config.py                # 설정 (DB_DIALECT, paths, thresholds)
│   │   ├── security.py              # MIME / 크기 검증
│   │   └── constants.py
│   ├── db/                          # DB 엔진 · 세션 · init
│   │   ├── base.py                  # DeclarativeBase
│   │   └── session.py               # SQLite / MariaDB engine, get_db, init_db
│   ├── models/                      # SQLAlchemy ORM (테이블)
│   │   ├── job.py                   # jobs
│   │   ├── feedback.py              # feedbacks
│   │   └── batch_job.py             # batch_jobs (Phase 2)
│   ├── schemas/                     # Pydantic API DTO
│   │   ├── request.py
│   │   ├── response.py
│   │   └── feedback.py
│   ├── repositories/                # DB 접근 전용
│   │   ├── job_repository.py
│   │   ├── feedback_repository.py
│   │   └── batch_repository.py
│   ├── routers/                     # HTTP 라우터 계층
│   │   ├── router.py                # /api/v1 집합
│   │   ├── upload.py
│   │   ├── feedback.py
│   │   ├── jobs.py                  # job 조회
│   │   └── batch.py
│   ├── workflows/                   # LangGraph
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── edges.py
│   │   └── graph.py
│   ├── services/
│   │   ├── image_processor.py
│   │   ├── segmentation.py
│   │   ├── effects.py
│   │   ├── validator.py
│   │   └── feedback_service.py      # DB repo + 파일 사이드카
│   ├── tasks/
│   │   └── batch_tasks.py
│   ├── utils/
│   └── exceptions.py
├── Dockerfile                       # 빌드 context = 저장소 루트
```

**Python 의존성(루트)**: `requirements.txt` (로컬 풀스택), `requirements.docker.txt` (경량 이미지)

**계층 규칙**: `routers` → `services`/`workflows` → `repositories` → `models`/`db`  
API 입출력은 `schemas`만 사용. ORM 모델은 Repository 밖으로 최대한 노출하지 않는다.

**DB**: 로컬 `SQLite` (`data/cutnkeep.db`) / 배포 `MariaDB` — 상세는 `docs/plan/DATABASE.md`  
**AI 모델**: yolo26s-seg + Ollama E4B(기본) / OpenAI·Gemini(고도화) — `docs/plan/AI_MODEL_STRATEGY.md`  
**테스트**: 루트 `tests/` + `pytest.ini` — `docs/plan/TESTING.md`


### 2.2 frontend/ (React + Vite)

```bash
frontend/
├── src/
│   ├── components/
│   │   ├── common/                  # Button, Modal 등
│   │   ├── image/
│   │   │   ├── ImageUploader.tsx
│   │   │   ├── BeforeAfterViewer.tsx
│   │   │   └── ProcessingStatus.tsx
│   │   ├── prompt/
│   │   │   └── PromptInput.tsx
│   │   ├── feedback/
│   │   │   └── FeedbackButtons.tsx
│   │   └── batch/
│   │       └── BatchUploader.tsx
│   ├── hooks/
│   │   ├── useImageProcessing.ts
│   │   └── useFeedback.ts
│   ├── store/                       # Zustand
│   │   └── useAppStore.ts
│   ├── api/
│   │   └── client.ts                # axios 인스턴스
│   ├── types/
│   │   └── index.ts
│   ├── utils/
│   │   └── formatters.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── tailwind.config.ts
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### 2.3 scripts/ & 기타

```bash
scripts/
├── fine_tune_lora.py                # LoRA 주기적 Fine-tuning
├── convert_to_onnx.py
├── pseudo_labeling.py
├── evaluate_model.py
└── cleanup.py                       # 24시간 후 임시 파일 삭제

docs/
├── plan/
│   ├── LOGIC_STRUCTURE.md           # 통합 로직
│   ├── PROJECT_STRUCTURE.md         # 본 문서
│   ├── DATABASE.md                  # SQLite / MariaDB · ERD · Repository
│   ├── LOGIC_AND_GIT_BRANCH_STRATEGY.md
│   ├── DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md
│   └── DEVELOPMENT_PLAN.docx
├── API_DOCUMENTATION.md
├── WORKFLOW.md
└── DEPLOYMENT.md


models/                              # .onnx, .safetensors 등
data/                                # 학습/피드백 데이터
docker/                              # Docker Compose 관련
logs/                                # 런타임 로그
```

---

## 3. 핵심 로직 흐름 (7단계)

1. **FastAPI 수신 + 보안 검증** (MIME, 크기, 파일 타입)
2. **LangGraph Prompt Analyzer** (LLM → JSON 구조화)
3. **OpenCV Preprocessing** (resize + CLAHE + 색공간 변환)
4. **Segmentation** (Phase1: YOLO-seg / Phase2: Grounding DINO + SAM2)
5. **Mask Refinement + Effect** (GrabCut, morphology, GaussianBlur, crop)
6. **Validator** (마스크 품질 체크 + fallback)
7. **결과 반환 + Feedback Loop** (실패 케이스 저장 → Pseudo Labeling → LoRA)

---

## 4. Phase별 개발 우선순위

**Phase 1 (MVP) – 현재 집중**
- `backend/app/services/image_processor.py` (OpenCV 7단계)
- `workflows/` 기본 구조 (LangGraph)
- FastAPI upload endpoint + 보안 검증
- React 업로드 + 결과 표시 + 피드백 버튼
- YOLO-seg ONNX 변환

**Phase 2**
- Grounding DINO + SAM2
- Celery + Redis 배치 처리 (최대 500장)
- 피드백 기반 Pseudo Labeling + LoRA Fine-tuning
- 진행률 표시 UI

**Phase 3**
- 영상 처리 + Optical Flow + LSTM Temporal Smoothing
- Docker + Nginx 배포
- 보안 강화 + 모니터링

---

## 5. 구조 설계 원칙 (실행 규칙 요약)

- **모듈화**: 각 서비스(image_processor, segmentation, effects 등)를 독립적으로 테스트 가능하게 분리
- **Phase 단위 확장**: Phase 1이 완전히 동작하기 전에 다음 Phase 기능을 넣지 않음
- **원본 보존**: OpenCV 모든 단계에서 `.copy()` 사용
- **메모리 효율**: 배치 처리는 반드시 Generator 방식
- **실패 자동 수집**: 모든 실패 케이스는 `data/feedback/`에 이미지 + JSON 자동 저장
- **설정 중앙화**: 경로·모델 이름은 `core/config.py` (Pydantic Settings)로 관리
- **보안**: 업로드 파일 MIME + 크기 검증 + 처리 후 24시간 자동 삭제

---

## 6. 이 구조의 장점

- 모듈화 극대화 → 각 서비스 독립 테스트 가능
- LangGraph로 워크플로우 확장성 높음
- Phase별 개발이 매우 용이
- 1인 개발자에게 유지보수 부담이 적음
- 피드백 루프를 처음부터 고려한 설계

---

**다음 액션 추천**
1. 이 구조로 실제 폴더 생성 (`mkdir -p` 명령)
2. `backend/app` skeleton 코드 생성
3. `image_processor.py`부터 구현 시작
4. Git 저장소 초기화 + `main` / `develop` 브랜치 생성

원하시면 바로 폴더 생성이나 skeleton 코드 작성을 진행해 드리겠습니다.
