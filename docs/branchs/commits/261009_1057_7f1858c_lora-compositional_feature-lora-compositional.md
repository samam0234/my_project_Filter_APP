# 조합형 학습 문장으로 처음 보는 문장 해석 개선 — 새 40문장 50.0→87.5% / `7f1858ce9d9d662bca4038265ff7a3a3c94c7c15`

> 브랜치: `feature/lora-compositional`  
> 작성일: `2026-10-09 10:57`  
> 작성자: `agent`  
> 파일명: `261009_1057_7f1858c_lora-compositional_feature-lora-compositional.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 조합형 학습 문장으로 처음 보는 문장 해석 개선 — 새 40문장 50.0→87.5%` |
| **커밋 번호 (SHA)** | `7f1858ce9d9d662bca4038265ff7a3a3c94c7c15` |
| **짧은 SHA** | `7f1858c` |
| **브랜치** | `feature/lora-compositional` |
| **부모 커밋** | `2eb74b5` |

## 2. 주 커밋 내용

- 조합형 시드 생성기 `training/lora/seed/build_compositional.py` → `train_compositional.jsonl`(899)
- 새 평가셋 `eval_fresh2.jsonl`(40, 생성기 전에 작성)
- 학습 기본 시드 · 평가 제외 · 재학습 판정 목록 갱신, 재학습 실행 · 배포본 교체

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "LoRA 개선". 10-08 배포본이 처음 보는 문장에서 대상 둘 누락 · 방해물 혼동 · 관계 표현 오해 · 자르기 말 · 어휘 부족으로 틀림.

### 3.2 변경 범위
- 추가: 생성기 · 시드 · 평가셋, `tests/unit/test_lora_compositional.py`, `docs/vaildates/lora-compositional-20261009.md` · `lora_retrain_20261009.json`
- 수정: `train_lora.py`, `scripts/retrain_lora.py`, 학습 README 2개, learning-loop, FEATURES, vaildates 색인

### 3.3 기술 포인트
- 오답 유형을 보고 설계했으므로 eval_fresh 상승은 부풀 수 있음 → 생성기 전에 쓴 eval_fresh2 로 확인 (p=0.0003)

### 3.4 의도적으로 하지 않은 것
- 기본 LLM_PROVIDER 변경 (체인 + LoRA 조합 미측정)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 테스트 430 통과
- [x] 평가셋 7개 하락 없음, +39문항

### 4.2 부작용 / 리스크
- 모델 파일은 git 밖 — 되돌리기 방법은 검증 문서에

### 4.3 후속 작업
- 체인 + LoRA 비교, selector 조합 생성

### 4.4 관련 문서
- `docs/vaildates/lora-compositional-20261009.md`
