# LLM 이 꺼졌을 때의 키워드 파서를 어휘 확장 + 역할 규칙으로 교체 (대상 56.6% → 100%) / `805f6d9d32a549c8d7d58d18f64754258d28dbde`

> 브랜치: `feature/leak-diagnosis`  
> 작성일: `2026-10-08 10:12`  
> 작성자: `agent`  
> 파일명: `261008_1012_805f6d9_heuristic-parser-roles_feature-leak-diagnosis.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(prompt): LLM 이 꺼졌을 때의 키워드 파서를 어휘 확장 + 역할 규칙으로 교체 (대상 56.6% → 100%)` |
| **커밋 번호 (SHA)** | `805f6d9d32a549c8d7d58d18f64754258d28dbde` |
| **짧은 SHA** | `805f6d9` |
| **브랜치** | `feature/leak-diagnosis` |
| **부모 커밋** | `03eb969` |

## 2. 주 커밋 내용

- LLM 이 꺼진 환경의 폴백 키워드 파서를 5종 대상 → 별칭표+COCO+일상어 어휘 + 역할 규칙으로 교체
- "X 말고 Y만", "A는 빼고", 쉼표/와·과/and 접속 역할 상속, 영어 앞쪽 동사
- 한 글자 낱말 오탐 방지(강도·산책·물건·차이)
- 효과 판정도 같은 역할 분석(예: "자동차만 지워줘 사람은 건드리지 말고" → remove_object)

## 3. 상세 내용

### 3.1 배경 / 목적
기존 폴백은 언급한 물체를 전부 대상으로 잡아 143문장 평가에서 대상 정확도 56.6%, 지정하지 않은 물체까지 대상에 넣는 "초과" 26건 — 섞임 증상의 문장 쪽 원인.

### 3.2 변경 범위
- 추가: `backend/app/services/heuristic_targets.py`, `tests/unit/test_heuristic_targets.py`, `training/lora/seed/eval_holdout.jsonl`(40)
- 수정: `workflows/nodes.py`(parse_prompt_heuristic 이 analyze 사용, 효과 동의어 확장), `parse_rounds.py`, `eval_distractor.jsonl`

### 3.3 기술 포인트
- 언급 뒤/앞 표지로 keep/erase/except/neutral 역할을 정함
- 규칙을 보며 고친 문장은 낙관적이므로 홀드아웃 40문장을 규칙 완성 뒤 한 번만 채점해 따로 기록

### 3.4 의도적으로 하지 않은 것
- LLM 경로 변경 없음(체인은 다음 커밋)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] pytest 359 통과
- 4개 셋 183문장 대상 100%·효과 96.2% (이전 56.6%·85.3%), 홀드아웃 39/40 (97.5%)

### 4.2 부작용 / 리스크
- 개발 문장 수치는 낙관적. 처음 보는 문장 수치는 후속 커밋에서 별도 측정

### 4.3 후속 작업
- 처음 보는 문장 평가, LangChain 다수결 체인

### 4.4 관련 문서
- `docs/vaildates/leak-diagnosis-20261008.md` (문장 해석 절)
