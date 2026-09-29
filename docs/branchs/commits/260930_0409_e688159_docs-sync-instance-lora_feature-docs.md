# 인스턴스 선택·LoRA·폴더 분리 반영 문서 전면 갱신 / `e688159faa709b66b6dec7775b5f050b1def75ec`

> 브랜치: `feature/docs`  
> 작성일: `2026-09-30 04:09`  
> 작성자: `agent`  
> 파일명: `260930_0409_e688159_docs-sync-instance-lora_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 인스턴스 선택·LoRA·폴더 분리 반영 문서 전면 갱신` |
| **커밋 번호 (SHA)** | `e688159faa709b66b6dec7775b5f050b1def75ec` |
| **짧은 SHA** | `e688159` |
| **브랜치** | `feature/docs` |
| **부모 커밋** | `4bb93fc` (feature/instance tip) |

## 2. 주 커밋 내용

- 경로 표기: SQLite·업로드 `backend/data/`, 서빙 가중치 `backend/models/`
- LLM 문서: "휴리스틱 기본 / 연동 예정" 제거, `lora` provider·타임아웃·평가 수치 추가
- 규격 문서: `selector`·`remove_object`·결과 `meta` 추적 필드 (API 문서 재작성)
- LoRA 문서: 새 기본 하이퍼·시드·평가·서빙 절차
- 테스트 목록·MVP 체크리스트·backend 서비스 모듈 표
- 디버그 일일 기록 `find_debug/2026-09-29.md` (6건)

## 3. 상세 내용

### 3.1 배경 / 목적

LLM 연동 → 폴더 분리 → 필터 수정 → 인스턴스 선택·LoRA 까지 코드가 크게 바뀌었지만
문서는 LLM 연동 이전 상태(휴리스틱 기본, 루트 `data/` 경로, 옛 LoRA 하이퍼)에 머물러 있었다.
`grep` 으로 어긋난 표현을 찾아 전부 맞췄다.

### 3.2 변경 범위

| 분류 | 파일 |
|------|------|
| 재작성 | `docs/guidance/llm-and-vision.md`, `docs/API_DOCUMENTATION.md`, `docs/WORKFLOW.md` |
| 부분 수정 | `docs/plan/AI_MODEL_STRATEGY.md`, `DATABASE.md`, `LOGIC_STRUCTURE.md`, `LOGIC_AND_GIT_BRANCH_STRATEGY.md`, `DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`, `TESTING.md`, `YOLO26S_DEFAULT.md` |
| 부분 수정 | `docs/Architecture/data-flow.md`, `overview.md`, `docs/guidance/getting-started.md`, `docs/trainings/phase1-pipeline.md`, `docs/vaildates/mvp-checklist.md`, `docs/README.md`, `docs/find_debug/README.md` |
| 루트·폴더 | `README.md`, `RUN.md`, `AGENTS.md`, `.agents/skills/cutnkeep/SKILL.md`, `backend/README.md`, `models/README.md`, `tests/README.md`, `training/README.md`, `training/configs/lora.example.yaml` |
| 추가 | `docs/find_debug/2026-09-29.md` |

### 3.3 기술 포인트

- `.env` 의 상대 경로 값은 그대로이므로 "값" 이 아니라 **기준(backend/ vs 루트)** 을 병기
- API 문서에 dislike 코멘트 JSON = LoRA 정답 경로를 명시 (프론트 "정답 알려주기" 와 연결)
- 평가 수치는 `training/lora/README.md` 표와 같은 값만 인용 (gemma 92.5% / LoRA 87.5% / 키워드 35%)

### 3.4 의도적으로 하지 않은 것

- 프론트엔드 문서(`frontend/README.md`, `docs/guidance/user-frontend.md`, `docs/Architecture/apps.md`)
  → 페이지 개편과 함께 `feature/frontend` 에서 갱신
- `docs/branchs/commits/` 과거 기록 수정 (당시 기준 기록이므로 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 옛 표현 재검색 결과 0건 (`q_proj,v_proj`, `gemma-2-2b`, `수동 구현 지점`, 루트 `data/uploads` 등)
- [x] pytest 전체 통과 (구조 테스트 포함)

### 4.2 부작용 / 리스크

- 없음 (문서만)

### 4.3 후속 작업

- `feature/frontend` 페이지 개편 + 프론트 문서
- develop 병합: instance → docs → frontend

### 4.4 관련 문서

- `docs/plan/CURRENT_STACK.md`
- `docs/guidance/llm-and-vision.md`
