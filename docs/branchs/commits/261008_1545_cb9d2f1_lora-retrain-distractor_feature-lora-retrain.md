# 방해물 문장 시드로 LoRA 재학습 — 판정 통과해 배포본 교체, 결과 문서 추가 / `cb9d2f192372f63038be0782df319572b5595a40`

> 브랜치: `feature/lora-retrain`  
> 작성일: `2026-10-08 15:45`  
> 작성자: `agent`  
> 파일명: `261008_1545_cb9d2f1_lora-retrain-distractor_feature-lora-retrain.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 방해물 문장 시드로 LoRA 재학습 — 판정 통과해 배포본 교체, 결과 문서 추가` |
| **커밋 번호 (SHA)** | `cb9d2f192372f63038be0782df319572b5595a40` |
| **짧은 SHA** | `cb9d2f1` |
| **브랜치** | `feature/lora-retrain` |
| **부모 커밋** | `d3d9b77` |

## 2. 주 커밋 내용

- `retrain_lora --force` 로 LoRA 재학습 (Qwen2.5-1.5B, 3 에폭, 시드 980 = `train` 800 + `train_distractor` 180, 평가 문장 41건은 학습에서 제외)
- 대상 정확도: 방해물 문장 78.7→95.7%, 홀드아웃 70.0→87.5%, 처음 본 30문장 70.0→73.3%, `eval_ext` 변화 없음
- 판정 통과(전체 +17문항, 최대 하락 1문항) → `backend/models/lora` 교체, 이전본 `backend/models/lora_prev_261008_1543` 보존
- 기본 `LLM_PROVIDER` 는 ollama 유지 (Ollama + 해석 체인이 처음 본 문장 96.7% 로 더 정확)
- 문서 `docs/vaildates/lora-retrain-20261008.md` · 점수 JSON, 학습 루프 문서와 검증 색인 갱신

## 3. 상세 내용

### 3.1 배경 / 목적
"X 말고 Y만" 같은 방해물 문장에서 LLM 이 지정하지 않은 대상을 섞는 문제를 LoRA 에도 학습시켜, Ollama 가 없는 환경의 대안 모델을 강화한다.

### 3.2 변경 범위
- 추가: `docs/vaildates/lora-retrain-20261008.md`, `docs/vaildates/lora_retrain_20261008.json`
- 수정: `docs/vaildates/README.md`, `docs/guidance/learning-loop.md`
- git 밖: `backend/models/lora`(교체), `backend/models/lora_prev_261008_1543`(이전본), `training/outputs/lora/user_261008_1509`(실행 산출물)

### 3.3 기술 포인트
- `--deploy` 로 다시 돌리면 학습을 처음부터 반복하므로, 같은 후보를 스크립트의 배포 절차(이전본 이동 → 후보 복사)대로 수동 교체하고 상태 파일에 배포 표시

### 3.4 의도적으로 하지 않은 것
- 기본 provider 를 lora 로 바꾸기 (정확도가 ollama + 체인보다 낮음)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 재학습·평가 정상 종료 (증강·학습·평가 합쳐 약 33분)
- [x] 판정: 채택

### 4.2 부작용 / 리스크
- 손실 0.0034 로 낮아 학습 문장을 외웠을 가능성 — 처음 보는 문장 셋에서는 떨어지지 않음
- 평가셋 30~56문장이라 1~2문항 차이는 잡음 범위

### 4.3 후속 작업
- 승인 문장이 쌓이면(현재 8개) 다시 재학습

### 4.4 관련 문서
- `docs/vaildates/lora-retrain-20261008.md`
