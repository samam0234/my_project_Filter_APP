# 해석 체인(LangChain)·어려운 사례 수집(LangGraph)·LoRA 방해물 시드, 콘솔에 설정 표시 / `fe8d736bf4f49c863ce78bc6f408aa5a90afd020`

> 브랜치: `feature/leak-diagnosis`  
> 작성일: `2026-10-08 10:30`  
> 작성자: `agent`  
> 파일명: `261008_1030_fe8d736_chain-hard-example-lora-seed_feature-leak-diagnosis.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(prompt): 해석 체인(LangChain)·어려운 사례 수집(LangGraph)·LoRA 방해물 시드, 콘솔에 설정 표시` |
| **커밋 번호 (SHA)** | `fe8d736bf4f49c863ce78bc6f408aa5a90afd020` |
| **짧은 SHA** | `fe8d736` |
| **브랜치** | `feature/leak-diagnosis` |
| **부모 커밋** | `805f6d9` |

## 2. 주 커밋 내용

- `prompt_chain.py`: LangChain Core Runnable 체인 — LLM 한 번 → 키워드 파서와 대상이 같으면 확정, 다르면 추가 질의 후 다수결(`PROMPT_CHAIN`, `PROMPT_VOTES`)
- LangGraph: 어려운 사례(`HARD_EXAMPLE_CONF`, 기본 꺼짐)를 `feedback_collector` 로 보내 학습 후보 저장, `meta.leak`·`hard_example` 기록
- LoRA: 시드에 `train_distractor.jsonl`(180), 평가셋에 `eval_distractor`·`eval_holdout` 추가(재학습 채택 판정 포함)
- 운영 콘솔 시스템 화면에 겹침 규칙·GrabCut·CLAHE·해석 체인 표시
- 학습 루프 문서와 검증 문서(leak-diagnosis) 초안, 라운드 원자료 JSON

## 3. 상세 내용

### 3.1 배경 / 목적
섞임 문제의 문장·학습 쪽 보강과 RAG·LangGraph·LangChain 에 새 학습 내용을 반영하는 경로 정리.

### 3.2 변경 범위
- 추가: `services/prompt_chain.py`, `tests/unit/test_prompt_chain.py`, `docs/guidance/learning-loop.md`, `docs/vaildates/leak_eval_*.json`, `training/lora/seed/train_distractor.jsonl`
- 수정: `config.py`, `edges.py`, `nodes.py`, `system_status.py`, 콘솔 SystemPage·types, `retrain_lora.py`, `train_lora.py`(seed-file 여러 개), 문서

### 3.3 기술 포인트
- 낮은 신뢰도 재시도 게이트는 같은 사진 쌍 비교에서 효과가 없어 코드를 지움(가설 폐기)
- 같은 문장이 학습과 평가에 겹치면 학습에서 뺌(점수 부풀림 방지)

### 3.4 의도적으로 하지 않은 것
- 체인은 기본 legacy 로 두고 평가 후 결정, LoRA 재학습은 실행하지 않음(파이프라인만 연결)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] pytest 367 · 콘솔 vitest 21 통과
- [x] Docker 재빌드 후 실제 업로드 API 29장: 섞임 7.6% (같은 30장 로컬 5.8%, 표본 오차 범위)

### 4.2 부작용 / 리스크
- HARD_EXAMPLE_CONF 를 켜면 회원 이미지가 더 저장됨(개인정보 안내·보관 기간 필요)

### 4.3 후속 작업
- 처음 보는 문장 평가 후 체인 기본값 결정

### 4.4 관련 문서
- `docs/guidance/learning-loop.md`, `docs/vaildates/leak-diagnosis-20261008.md`
