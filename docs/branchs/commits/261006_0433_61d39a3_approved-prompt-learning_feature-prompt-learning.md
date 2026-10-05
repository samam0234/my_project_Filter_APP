# 승인된 사용자 문장 학습·증강과 어휘 정규화 / `61d39a3d073767309240f7d347f0827a7c69bbfc`

> 브랜치: `feature/prompt-learning`  
> 작성일: `2026-10-06 04:33`  
> 작성자: `agent`  
> 파일명: `261006_0433_61d39a3_approved-prompt-learning_feature-prompt-learning.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 승인된 사용자 문장 학습·증강과 어휘 정규화` |
| **커밋 번호 (SHA)** | `61d39a3d073767309240f7d347f0827a7c69bbfc` |
| **짧은 SHA** | `61d39a3` |
| **브랜치** | `feature/prompt-learning` |
| **부모 커밋** | `7570911` (feature/feedback-review) |

## 2. 주 커밋 내용

- LoRA 학습이 학습 DB 의 **승인된** 사용자 문장 + 증강 문장을 사용
- 증강 스크립트 (같은 뜻 다른 표현 + 자기 일치 검증)
- 확장 평가셋 56건, 평가셋 누수 차단
- 파서 출력 어휘 정규화 (COCO 대상 이름 · effect 별칭)

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청: "사용자의 프롬프트를 가지고 학습해서 LLM 을 강화해 이미지 작업을 더 실용적으로".
검수 콘솔(`feature/feedback-review`)로 모인 승인 문장을 학습 경로에 연결하고, 효과를 정직하게 측정.

### 3.2 변경 범위

- 추가: `training/lora/augment_prompts.py`, `training/lora/seed/eval_ext.jsonl`
- 수정: `training/lora/{dataset,train_lora,eval_parser}.py`, `backend/app/services/prompt_spec.py`,
  `tests/unit/{test_lora_dataset,test_prompt_llm}.py`, `training/lora/README.md`,
  `docs/guidance/{llm-and-vision,console-admin}.md`

### 3.3 기술 포인트

- 운영 판단(agent): 실제 회원 요청 후보 9건을 검수 — 7건 승인, 안전모·조끼 2건은 selector 누락이라
  평가셋 정답과 같은 값으로 고쳐 승인 (콘솔에서 되돌리기 가능, reviewed_by=agent)
- 증강: 생성 64 → 채택 61 (뜻 바뀜 3) → 평가셋 문장 원문 3건의 증강 22건 제거 → 39건
- 누수: 의사 라벨 32건이 평가 문장 "사람만 남기고 배경 블러" 와 같았음 → 학습에서 자동 제외
- 비교 실험: v3 와 같은 설정에서 사용자 데이터만 뺀 `instance_v3_nouser` 를 따로 학습

### 3.4 의도적으로 하지 않은 것

- v3 배포 — v2 와 차이가 잡음 수준 (합계 96문항 82 vs 83)
- LoRA 학습 템플릿 변경 (재학습 필요)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 파서 | eval 40 | eval_ext 56 |
|------|---------|-------------|
| ollama gemma4:e4b | 92.5% | 85.7% → **91.1%** (정규화) |
| LoRA v2 (배포) | 87.5% | 80.4% → 83.9% |
| LoRA v3 (사용자 데이터 포함) | 92.5% | 78.6% → 82.1% |
| LoRA v3_nouser | 92.5% | 80.4% (정규화 전) |

- 사용자 문장 학습 효과: **측정되지 않음** (승인 8건) — v2→v3 상승은 재학습 차이
- 실효 개선: 어휘 정규화로 Ollama 파싱 실패 3건 → 0, LoRA COCO 밖 이름 교정
- [x] pytest 전체 통과

### 4.2 부작용 / 리스크

- `canonical_target` 이 마지막 단어로 맞추므로 드물게 다른 클래스로 갈 수 있음 (예: 모르는 합성어)
- SYSTEM_PROMPT 변경 → Ollama 해석이 조금 달라질 수 있음 (평가로 확인)

### 4.3 후속 작업

- 완성도 5번 실험 (부하·동시 요청, 실제 이미지 end-to-end)
- 승인 문장이 수백 건 쌓이면 v4 학습·재측정

### 4.4 관련 문서

- `training/lora/README.md` (확장 평가셋 · 사용자 문장 학습)
- `docs/guidance/llm-and-vision.md` (어휘 정규화)
