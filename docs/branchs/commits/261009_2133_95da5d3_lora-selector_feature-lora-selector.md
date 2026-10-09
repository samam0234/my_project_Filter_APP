# 개수 + 위치 선택자 조합 문장으로 재학습 — 선택자 새 30문장 33.3→96.7% / `95da5d34e2f53f3bff16857870cf66cdb8451027`

> 브랜치: `feature/lora-selector`  
> 작성일: `2026-10-09 21:33`  
> 작성자: `agent`  
> 파일명: `261009_2133_95da5d3_lora-selector_feature-lora-selector.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 개수 + 위치 선택자 조합 문장으로 재학습 — 선택자 새 30문장 33.3→96.7%` |
| **커밋 번호 (SHA)** | `95da5d34e2f53f3bff16857870cf66cdb8451027` |
| **짧은 SHA** | `95da5d3` |
| **브랜치** | `feature/lora-selector` |
| **부모 커밋** | `98fad0e` |

## 2. 주 커밋 내용

- 조합형 생성기 선택자 묶음, 새 평가셋 eval_fresh3
- 재학습 · 배포본 교체, 해석기 재비교

## 3. 상세 내용

### 3.1 배경 / 목적
남은 작업 "selector 조합(개수 + 위치, N마리 중 큰)" — lora-compositional 문서의 다음 단계.

### 3.2 변경 범위
- 추가: `training/lora/seed/eval_fresh3.jsonl`, `docs/vaildates/lora-selector-20261009.md` · 원자료 3개
- 수정: `build_compositional.py` · `train_compositional.jsonl`, `train_lora.py`, `retrain_lora.py`, `parser_compare.py`, `test_lora_compositional.py`, 문서

### 3.3 기술 포인트
- 평가셋을 생성 템플릿보다 먼저 작성, 문항 단위 쌍 비교(부호 검정)로 확인

### 3.4 의도적으로 하지 않은 것
- 기본 LLM_PROVIDER 변경 (실제 사용자 문장 · GPU 서버 여부 미정)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 통과
- [x] fresh3 33.3→96.7%, 283문장 LoRA 94.7% vs Ollama 체인 85.2%

### 4.2 부작용 / 리스크
- 모델 파일은 git 밖 — 되돌리기는 검증 문서

### 4.3 후속 작업
- 승인 문장으로 재비교 후 GPU 서버 기본값 결정

### 4.4 관련 문서
- `docs/vaildates/lora-selector-20261009.md`
