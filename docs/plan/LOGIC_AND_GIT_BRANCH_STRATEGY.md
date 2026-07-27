# 컷앤킵 (Cut & Keep)
로직 구조 + 프로젝트 실행 규칙 + Git 브랜치 전략

**한 줄 설명**  
프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

**프로젝트 목적**  
AI 학습 데이터 준비 시 bounding box를 수작업으로 그리는 번거로움과 한계를 해결하기 위해,  
자연어 프롬프트만으로 특정 물체(사람·동물·물건)만 정확하게 추출·필터링해주는 도구를 만든다.

---

## 1. 전체 로직 구조 (최신 계획서 기준)

### 1.1 핵심 처리 흐름 (7단계)

```
[Frontend] React 업로드 + 프롬프트 입력
        ↓
[1] FastAPI 수신 + 보안 검증
    - MIME 타입 / 파일 크기 / 확장자 검증
        ↓
[2] LangGraph Prompt Analyzer (LLM)
    - 자연어 프롬프트를 JSON으로 구조화
    - 예: {"target": ["dog"], "effect": "blur", "intensity": 15, "crop": false}
        ↓
[3] OpenCV Preprocessing
    - imread, resize (종횡비 유지)
    - CLAHE 대비 향상 (clipLimit=2.0, tileGridSize=(8,8))
    - 색공간 변환
        ↓
[4] Segmentation
    - Phase 1 : YOLOv8-seg / YOLO11-seg (ONNX)
    - Phase 2 : Grounding DINO + SAM2 (텍스트 프롬프트 기반 정밀 마스크)
        ↓
[5] Mask Refinement + Effect Application
    - GrabCut + morphologyEx (MORPH_CLOSE)
    - GaussianBlur + bitwise_and (배경 블러)
    - boundingRect + crop
    - 알파 채널 합성 / addWeighted
        ↓
[6] Validator
    - 마스크 품질 체크 (면적, confidence)
    - 실패 시 fallback 로직 실행
        ↓
[7] 결과 반환 + Feedback Loop
    - Before / After 이미지 반환
    - 사용자 피드백(좋아요/싫어요) → 실패 케이스 자동 저장
    - Pseudo Labeling → 주기적 LoRA Fine-tuning
```

### 1.2 LangGraph 노드 구성

| 노드                  | 역할                              | 주요 기술                     |
|-----------------------|-----------------------------------|-------------------------------|
| prompt_analyzer       | 프롬프트 → JSON 구조화            | LangChain + LLM               |
| preprocessor          | CLAHE, resize, 색공간 변환        | OpenCV                        |
| segmentor             | 객체 마스크 생성                  | YOLO / GroundingDINO + SAM2   |
| effect_applier        | 블러 / 크롭 / 마스크 합성         | OpenCV                        |
| validator             | 품질 검증 + fallback              | 커스텀 로직                   |
| feedback_collector    | 실패 케이스 저장 + Pseudo Label   | 파일 시스템 + JSON            |

### 1.3 배치 처리 (최대 500장)
- Celery + Redis 큐 사용
- Generator 방식으로 메모리 효율화
- 실시간 진행률은 WebSocket 또는 SSE로 전달

### 1.4 영상 처리 (Phase 3)
- 프레임 단위로 위 7단계 적용
- Optical Flow + LSTM/GRU 기반 Temporal Smoothing으로 마스크 흔들림 제거

---

## 2. 프로젝트 실행 규칙 (Development Rules)

1인 개발 + 현실적 구현을 위한 **필수 준수 규칙**입니다.

### 2.1 기본 개발 원칙
- **Phase 단위로만 확장한다.** (Phase 1이 완전히 동작하기 전에 Phase 2 기능을 넣지 않는다)
- 완전 자동 무한 학습보다는 **가벼운 피드백 기반 개선(LoRA)** 방식을 유지한다.
- 기술적으로 과도하게 복잡하지 않으면서도 차별화가 느껴지도록 설계한다.
- 모든 기능은 “동작하는 최소 단위”부터 만들고, 점진적으로 고도화한다.

### 2.2 코드 작성 규칙
- Python: Black + isort 포맷 강제, type hint 필수
- React: TypeScript strict 모드, 함수형 컴포넌트 + hooks만 사용
- 모든 OpenCV 단계에서 `.copy()`로 원본 이미지를 보존한다.
- 배치 처리 시 반드시 Generator / 스트리밍 방식을 사용해 메모리 초과를 방지한다.
- 실패 케이스는 무조건 `data/feedback/`에 이미지 + JSON으로 자동 저장한다.
- 하드코딩된 경로/모델 이름은 `core/config.py` (Pydantic Settings)로 관리한다.

### 2.3 보안 & 파일 처리 규칙
- 업로드 파일은 MIME 타입 + 확장자 + 크기(기본 20MB) 검증을 반드시 통과해야 한다.
- 처리가 끝난 파일은 24시간 후 자동 삭제한다. (임시 파일은 즉시 삭제)
- 사용자 업로드 파일은 절대 영구 저장하지 않는다. (피드백 실패 케이스만 별도 보관)

### 2.4 모델 & 성능 규칙
- Phase 1에서는 YOLO-seg + ONNX Runtime만 사용한다.
- Grounding DINO + SAM2는 Phase 2에서만 도입한다.
- LoRA Fine-tuning은 주 1회 오프라인(Colab)으로 실행하고, 가중치만 교체한다.
- 추론 속도가 느려지면 즉시 ONNX 변환 또는 모델 경량화를 우선 검토한다.

### 2.5 Git & 브랜치 규칙
- 모든 작업은 `develop`에서 파생된 `feature/*` 브랜치에서만 진행한다.
- `main`에는 오직 `release/*` 또는 `hotfix/*`만 merge한다.
- Feature 브랜치는 1~2주 이내에 끝내고 develop에 merge 후 삭제한다.
- 커밋 메시지는 Conventional Commits 형식을 따른다.  
  예: `feat(opencv): CLAHE + GrabCut 파이프라인 구현`

### 2.6 문서화 규칙
- 새로운 기능 추가 시 반드시 `docs/` 또는 해당 feature 브랜치에서 문서도 함께 업데이트한다.
- 계획서와 실제 구현이 달라지면 즉시 이 문서와 계획서를 동기화한다.

---

## 3. Git 브랜치 전략 (1인 개발 최적화)

### 3.1 브랜치 계층

```
main                    ← 최종 배포용 (Production)
│
├── develop             ← 일상 통합 개발 브랜치
│   │
│   ├── feature/*       ← 기능 단위 작업
│   ├── bugfix/*
│   └── hotfix/*
│
├── release/*           ← 배포 직전 검증
│
└── experimental/*      ← 모델 실험 / 테스트
```

### 3.2 주요 Feature 브랜치

| 브랜치                     | 용도                                      |
|---------------------------|-------------------------------------------|
| `feature/frontend`        | React UI, 업로드, Before/After, 피드백 버튼 |
| `feature/backend`         | FastAPI 엔드포인트, 보안, 파일 처리         |
| `feature/opencv`          | CLAHE, GrabCut, Blur, 마스크 합성           |
| `feature/yolo`            | YOLOv8/11-seg ONNX 통합                     |
| `feature/langgraph`       | LangGraph 워크플로우 전체                   |
| `feature/llm`             | 프롬프트 분석 LLM                           |
| `feature/sam2`            | Grounding DINO + SAM2 (Phase 2)             |
| `feature/batch`           | Celery + Redis 배치 처리                    |
| `feature/feedback`        | 피드백 수집 + Pseudo Labeling               |
| `feature/lora`            | LoRA Fine-tuning 스크립트                   |
| `feature/video`           | 영상 처리 + Temporal Smoothing (Phase 3)    |
| `feature/docs`            | 문서, README, 계획서                        |
| `feature/models`          | 모델 파일 / ONNX 변환                       |
| `feature/scripts`         | 유틸 스크립트                               |

### 3.3 작업 흐름 요약
```
develop → feature/xxx 생성 → 작업 완료 → develop merge → 
충분히 안정되면 release/* → main merge → 태그 생성
```

---

## 4. Phase별 우선순위 (실행 순서)

**Phase 1 (MVP) – 지금 당장 집중**
1. `feature/opencv` + `feature/yolo`
2. `feature/langgraph` (기본 워크플로우)
3. `feature/backend` (업로드 엔드포인트)
4. `feature/frontend` (업로드 + 결과 표시 + 피드백 버튼)

**Phase 2**
- `feature/sam2`, `feature/batch`, `feature/feedback`, `feature/lora`

**Phase 3**
- `feature/video` + Docker 배포

---

## 5. 다음 액션 추천

1. 이 문서를 기준으로 Git 저장소 초기화 (`main` + `develop`)
2. Phase 1 핵심 브랜치부터 생성
3. `feature/opencv`부터 skeleton 코드 작성 시작

원하시면 바로 다음 단계로 진행해 드리겠습니다.
