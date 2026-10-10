# 파이프라인 비차단 실행·재시도 전략·모델 워밍업 / `6f443645bdaf1c561bb0ab471e684e1c0a73ef22`

> 브랜치: `feature/langgraph`  
> 작성일: `2026-10-04 04:05`  
> 작성자: `agent`  
> 파일명: `261004_0405_6f44364_pipeline-nonblocking-retry-warmup_feature-langgraph.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(langgraph): 파이프라인 비차단 실행·재시도 전략·모델 워밍업` |
| **커밋 번호 (SHA)** | `6f443645bdaf1c561bb0ab471e684e1c0a73ef22` |
| **짧은 SHA** | `6f44364` |
| **브랜치** | `feature/langgraph` |
| **부모 커밋** | `8f8bbd4` (develop) |

## 2. 주 커밋 내용

- 업로드 파이프라인을 스레드풀에서 실행 (이벤트 루프 차단 해소) + YOLO 추론 잠금
- 재시도 조건 변경 (CLAHE 없는 원본 축소본 + 신뢰도 ×0.6) + 두 시도 중 최선 채택
- 노드별 소요 시간 `meta.timings` · 로그
- 기동 시 모델 미리 로드 + 워밍업 추론 (`PRELOAD_MODELS`)

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 질문 "RAG·LangGraph 가 잘 적용됐나, 고도화하자". 점검 결과 LangGraph 는 실제로 컴파일·실행되고 있었지만
(1) async 라우터에서 동기 파이프라인을 호출해 처리 중 서버 전체가 멈췄고
(2) 재시도가 같은 입력·같은 기준이라 결과가 항상 같았다. RAG 는 없음 (`feature/rag` 에서 추가).

### 3.2 변경 범위

- 수정: `backend/app/{main.py, core/config.py, routers/upload.py, services/segmentation.py, workflows/{graph,nodes,state}.py}`,
  `.env.example`, `docs/{WORKFLOW,API_DOCUMENTATION}.md`, `docs/plan/CURRENT_STACK.md`, `tests/unit/test_segmentation_filter.py`
- 추가: `tests/unit/test_pipeline_graph.py`

### 3.3 기술 포인트

- `graph.NODES`: 이름 → `_timed` 래핑 노드. LangGraph 그래프와 선형 fallback 이 같은 표를 써서 타이밍 일관
- 최선 시도 선택은 인덱스 기준 — dict 안 numpy 마스크를 `list.index` 로 비교하면 오류 (테스트로 발견·수정)
- `ImageProcessor` 싱글톤은 미리 로드 스레드와 요청 스레드 경합을 이중 확인 잠금으로 방지
- 첫 YOLO 추론의 GPU/런타임 초기화(약 11 s)는 모델 로드와 별개 → 빈 이미지 추론으로 워밍업

### 3.4 의도적으로 하지 않은 것

- LangGraph 스트리밍으로 실시간 진행률 전송 (프론트는 경과 시간 기반 단계 표시 유지)
- 동시 처리 개수 제한 (스레드풀 기본값)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 측정 (실서버, 기동 직후 첫 요청) | 수정 전 | 미리 로드 | + 워밍업 |
|---|---|---|---|
| 전체 | 71.0 s | 22.0 s | **4.5 s** |
| preprocessor | 21.3 s | 0.37 s | 0.11 s |
| segmentor | 12.2 s | 11.7 s | 0.15 s |

- [x] 처리 중 `/health` 7회 평균 11 ms (이전: 파이프라인 동안 대기)
- [x] pytest 전체 통과 (신규 4개)

### 4.2 부작용 / 리스크

- 기동 시 백그라운드로 GPU 메모리를 바로 잡음 (`PRELOAD_MODELS=false` 로 끔)
- YOLO 추론은 잠금으로 직렬화 — 동시 요청이 많으면 세그 단계에서 대기

### 4.3 후속 작업

- `feature/rag`: 프롬프트 해석 RAG

### 4.4 관련 문서

- `docs/WORKFLOW.md`
