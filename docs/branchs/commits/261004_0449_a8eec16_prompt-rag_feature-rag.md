# 프롬프트 해석 RAG로 사용자 교정 즉시 반영 / `a8eec1624dff851774ba0997fb60a1dc43fb887d`

> 브랜치: `feature/rag`  
> 작성일: `2026-10-04 04:49`  
> 작성자: `agent`  
> 파일명: `261004_0449_a8eec16_prompt-rag_feature-rag.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(rag): 프롬프트 해석 RAG로 사용자 교정 즉시 반영` |
| **커밋 번호 (SHA)** | `a8eec1624dff851774ba0997fb60a1dc43fb887d` |
| **짧은 SHA** | `a8eec16` |
| **브랜치** | `feature/rag` |
| **부모 커밋** | `c47b9ab` (feature/langgraph) |

## 2. 주 커밋 내용

- `services/prompt_rag.py`: 사용자 교정·좋아요를 지식 베이스로, 비슷한 문장의 정답을 LLM 지시문에 예시로 붙임
- `prompt_analyzer` 노드에 연결 (ollama · openai · gemini), `meta.prompt_rag` 에 출처·점수만 기록
- `eval_parser.py --parsers ollama_rag` 추가, 평가로 기본값 결정 (시드 제외, 임계 0.6)

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청 "RAG·LangGraph 고도화". RAG 는 없었다. 사용자가 "정답 알려주기"로 교정해도
LoRA 를 다시 학습하기 전까지 해석에 반영되지 않았다 → 교정을 검색해 바로 예시로 쓰게 함.

### 3.2 변경 범위

- 추가: `backend/app/services/prompt_rag.py`, `tests/unit/test_prompt_rag.py`
- 수정: `backend/app/{core/config.py, services/prompt_llm.py, workflows/{graph,nodes,state}.py}`,
  `training/lora/{eval_parser.py, README.md}`, `.env.example`,
  `docs/{WORKFLOW.md, guidance/llm-and-vision.md, plan/CURRENT_STACK.md}`, `tests/unit/{test_pipeline_graph,test_prompt_llm}.py`

### 3.3 기술 포인트

- 검색: 글자 2·3-gram TF-IDF 코사인 — 외부 임베딩 모델·의존성 없이 한국어 짧은 문장에 동작
- 버그 수정: 지식 베이스에 없는 n-gram 을 질의 벡터에서 빼면 질의의 안 맞는 부분이 점수를 깎지 못함
  ("왼쪽 세 번째 자전거만 남기고 배경 제거" ↔ "사람만 남기고 배경 제거" 0.88 → 0.40)
- 같은 문장은 교정 > 좋아요 > 시드 하나만, `pipeline_failure` 제외
- 피드백 폴더 서명(파일 수·최신 mtime)이 바뀌면 재색인
- 개인정보: 다른 사용자의 문장은 LLM 예시로만 쓰고 결과 meta 에는 남기지 않음

### 3.4 의도적으로 하지 않은 것

- 시드 800건을 예시로 쓰기 — 평가에서 정확도를 낮춤 (`PROMPT_RAG_SOURCES` 에 `seed` 를 넣으면 사용 가능)
- 임베딩 모델 기반 검색 (지식 베이스가 작아 n-gram 으로 충분, 의존성 증가)

## 4. 커밋 관련 결과

### 4.1 동작 결과

평가 `seed/eval.jsonl` 40건, gemma4:e4b (평가 문장과 같은 예시는 제외):

| 구성 | 완전 일치 |
|------|-----------|
| RAG 없음 | 95.0% |
| 시드 포함 (top 4, 0.2) | 90.0% |
| 시드 포함 + 지시 문구 보강 (top 3, 0.3) | 92.5% |
| 교정·좋아요만 (현재 피드백, 0.6) | 92.5% (추가 오답 1건은 예시 없는 요청 → Ollama 흔들림) |
| 교정·좋아요만 + 비슷한 표현 교정 2건 | **97.5%** |

- [x] pytest 전체 통과 (RAG 7건 신규)

### 4.2 부작용 / 리스크

- 잘못된 교정도 비슷한 요청에 그대로 예시로 쓰임 (모든 사용자 공통) — 운영 콘솔에서 피드백 검토 필요
- 요청마다 지시문이 길어짐 (예시가 붙을 때만, 최대 3줄)

### 4.3 후속 작업

- 운영 콘솔에서 교정 피드백 승인·삭제
- 평가셋 확대 (40건은 ±1건 흔들림에 2.5%p 가 움직임)

### 4.4 관련 문서

- `docs/guidance/llm-and-vision.md` (프롬프트 해석 RAG)
- `docs/WORKFLOW.md`
