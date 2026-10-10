# 재학습 판정에 처음 보는 30문장(eval_fresh) 평가셋 추가 / `d3d9b7711d393e98ee2b61c79a9a553b77219e7a`

> 브랜치: `feature/lora-retrain`  
> 작성일: `2026-10-08 15:09`  
> 작성자: `agent`  
> 파일명: `261008_1509_d3d9b77_lora-eval-fresh-gate_feature-lora-retrain.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 재학습 판정에 처음 보는 30문장(eval_fresh) 평가셋 추가` |
| **커밋 번호 (SHA)** | `d3d9b7711d393e98ee2b61c79a9a553b77219e7a` |
| **짧은 SHA** | `d3d9b77` |
| **브랜치** | `feature/lora-retrain` |
| **부모 커밋** | `ad27964` |

## 2. 주 커밋 내용

- `scripts/retrain_lora.py` 의 채택 판정 평가셋에 `eval_fresh`(30) 추가 → 다섯 평가셋 모두에서 1문항 넘게 떨어지지 않아야 채택
- `training/lora/train_lora.py` 기본 평가셋에도 추가 → 같은 문장이 학습에 섞이면 학습에서 뺌

## 3. 상세 내용

### 3.1 배경 / 목적
해석 체인을 만든 뒤 처음 쓴 30문장은 LoRA 가 본 적 없는 문장이라, 재학습 판정에서 일반화를 확인하는 데 쓴다.

### 3.2 변경 범위
- 수정: `scripts/retrain_lora.py`, `training/lora/train_lora.py`

### 3.3 기술 포인트
- 평가 문장 누수 방지(`drop_eval_leaks`)는 평가셋 목록을 그대로 쓰므로 목록에 넣는 것만으로 적용된다

### 3.4 의도적으로 하지 않은 것
- 판정 기준(최대 하락 1문항) 변경 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 다음 커밋의 재학습에서 다섯 평가셋 + 승인 val 로 판정 수행 확인

### 4.2 부작용 / 리스크
- 평가셋이 늘어 재학습 1회 평가 시간이 약 20% 늘어남

### 4.3 후속 작업
- 재학습 실행(cb9d2f1)

### 4.4 관련 문서
- `docs/guidance/learning-loop.md`
