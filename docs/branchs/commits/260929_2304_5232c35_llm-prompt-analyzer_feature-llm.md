# 프롬프트 분석 LLM 연동 추가 / `5232c3500725fe6c5250b8a58863b5b3c7da9e7d`

> 브랜치: `feature/llm`  
> 작성일: `2026-09-29 23:04`  
> 작성자: `agent`  
> 파일명: `260929_2304_5232c35_llm-prompt-analyzer_feature-llm.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(llm): 프롬프트 분석 LLM 연동 추가` |
| **커밋 번호 (SHA)** | `5232c3500725fe6c5250b8a58863b5b3c7da9e7d` |
| **짧은 SHA** | `5232c35` |
| **브랜치** | `feature/llm` |
| **부모 커밋** | `027f06d` (develop) |

## 2. 주 커밋 내용

- `prompt_analyzer` 노드에 LLM 분기 연결 (Phase 1 하드코딩 1순위 완료)
- `services/prompt_llm.py` 신규: Ollama·OpenAI·Gemini 호출 + JSON 추출·정규화
- provider 가 heuristic/빈 값이거나 호출·파싱 실패 시 휴리스틱 fallback
- 실제 사용 파서를 `state.prompt_parser` / 결과 `meta.prompt_parser` 에 기록
- `LLM_TIMEOUT_SECONDS` 설정 추가 (기본 30초)
- 네트워크 없는 단위 테스트 21개 추가

## 3. 상세 내용

### 3.1 배경 / 목적

휴리스틱 파서는 키워드 사전(person/dog/cat/car/bag)에 없는 대상을 모두 `person` 으로
처리해 "머그컵만 남겨", "노트북이랑 폰만" 같은 요청을 잘못 해석했다.
LLM 이 자연어를 YOLO(COCO) 클래스명으로 변환하도록 해 이 한계를 메운다.

### 3.2 변경 범위

- 추가된 경로:
  - `backend/app/services/prompt_llm.py`
  - `tests/unit/test_prompt_llm.py`
- 수정된 경로:
  - `backend/app/workflows/nodes.py` (하드코딩 구간 → LLM 분기 구현)
  - `backend/app/workflows/state.py`, `backend/app/workflows/graph.py` (`prompt_parser`)
  - `backend/app/core/config.py` (`llm_timeout_seconds`, 안내 블록 정리)
  - `.env.example`, `docs/plan/HARDCODING_ZONES.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트

- Docker 경량 이미지(`requirements.docker.txt`)에 langchain/httpx 가 없어 표준 `urllib` 사용
- Ollama 는 native `/api/chat` + `format: json` + `temperature: 0`
- 응답 정규화: target 소문자·중복 제거, intensity 0~100 클램프, effect 허용 목록 검증
  (범위 밖이면 `LLMError` → 휴리스틱이 더 믿을 만하다고 판단)
- effect=crop 이면 crop=True 로 맞춤 (휴리스틱과 동일 규칙)
- 시스템 프롬프트의 target 어휘는 COCO names 기준 (커스텀 클래스 추가 시 함께 수정)

### 3.4 의도적으로 하지 않은 것

- LLM 결과 캐시 (동일 프롬프트 재호출 최적화)
- 비동기/스트리밍 호출 — 현재 동기 호출이라 업로드 응답 시간에 LLM 지연이 더해짐
- ONNX 추론, 학습·평가 루프 (후속)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 로컬 pytest 전체 통과 (신규 21개 포함)
- [x] 실제 Ollama `gemma4:e4b` 로 6개 프롬프트 해석 확인
  - "저 빨간 머그컵만 남기고 크롭해줘" → `cup`, crop (휴리스틱은 `person`)
  - "노트북이랑 폰만 남기고 배경 흐리게 강도 60" → `laptop, cell phone`, blur, 60
- [ ] Docker 확인 (미실시)
- 요청 1건 LLM 지연 약 2.5~12초 (첫 호출은 모델 로드로 느림)

### 4.2 부작용 / 리스크

- LLM 지연이 업로드 응답에 그대로 반영됨 → `LLM_TIMEOUT_SECONDS` 조정 또는 `LLM_PROVIDER=heuristic`
- 모델이 COCO 밖 이름(예: `mug`)을 낼 수 있음 — 이 경우 YOLO 라벨과 안 맞아 stub/실패로 떨어질 수 있음
- Docker backend 는 `host.docker.internal:11434` 로 Ollama 접근 필요

### 4.3 후속 작업

- ONNX 세션·predict 분기, 학습·평가 루프, 배치 워커
- 필요 시 LLM 결과 캐시·타임아웃 튜닝

### 4.4 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/HARDCODING_ZONES.md`
