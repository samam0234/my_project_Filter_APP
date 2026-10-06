# 승인 데이터 재학습 루프와 콘솔 진행 표시 / `380a639c177a15072154c4fb8d372164b100802a`

> 브랜치: `feature/retrain-loop`  
> 작성일: `2026-10-06 18:31`  
> 작성자: `agent`  
> 파일명: `261006_1831_380a639_retrain-loop_feature-retrain-loop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 승인 데이터 재학습 루프와 콘솔 진행 표시` |
| **커밋 번호 (SHA)** | `380a639c177a15072154c4fb8d372164b100802a` |
| **짧은 SHA** | `380a639` |
| **브랜치** | `feature/retrain-loop` |
| **부모 커밋** | `d3cfe33` (feature/ui-check) |

## 2. 주 커밋 내용

- `scripts/retrain_lora.py` — 승인 문장이 기준 이상 쌓이면 증강·학습·평가·배포본 비교를 한 번에
- 콘솔 승인 카드 "재학습 N/200"

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 "다음 할 일" 4번 — 실제 사용으로 학습 데이터를 쌓고 수백 건이 되면 LoRA 재학습·재측정.
실제 데이터는 지어낼 수 없으므로, 데이터가 쌓였을 때 사람이 손대지 않아도 도는 루프를 만들었다.

### 3.2 변경 범위

- 추가: `scripts/retrain_lora.py`
- 수정: `backend/app/{core/config.py, routers/console.py, services/learning_review.py}`,
  `console/src/{pages/LearningPage.tsx, types/index.ts}`, `tests/unit/test_lora_dataset.py`,
  `training/lora/README.md`, `docs/guidance/console-admin.md`, `scripts/README.md`, `.env.example`

### 3.3 기술 포인트

- 판정 `decide()`: 전체 맞힌 수 증가 **그리고** 어느 평가셋도 `--max-drop`(1) 넘게 하락하지 않음 — 평가셋이 작아 재학습만으로 1~2문항 흔들리기 때문
- `--deploy` 일 때만 `backend/models/lora` 교체, 이전 본은 `lora_prev_<시각>` 로 백업
- 상태 파일 `training/outputs/lora/retrain_state.json` 에 학습에 쓴 승인 샘플 id
- 브랜치는 `feature/ui-check` 위에 쌓음 (ui-check 에서 추가한 `USER_SOURCES` 사용)

### 3.4 의도적으로 하지 않은 것

- 스케줄 등록 (OS 작업 스케줄러·cron 은 배포 환경에서)
- 자동 배포 기본값 (사람이 `--deploy` 로 결정)

## 4. 커밋 관련 결과

### 4.1 동작 결과

점검 실행 `python scripts/retrain_lora.py --force` (`user_261006_1802`):

| 평가셋 | 배포본(v2) | 후보 |
|--------|-----------|------|
| eval (40) | 87.5% | 87.5% |
| eval_ext (56) | 83.9% | 82.1% |
| 승인 val (1) | 100% | 100% |

- 판정: **불채택** (전체 −1문항) → 배포본 유지. 승인 데이터 8건이라 예상된 결과, 루프는 정상 동작
- 기준 미만일 때: "재학습 대기 — 192건 더 승인되면 진행"
- [x] pytest 전체 통과 (신규 1건), console vitest 4 · 빌드 성공

### 4.2 부작용 / 리스크

- 한 바퀴 약 30분 (증강 · 학습 · 평가 6회), 그동안 GPU 사용

### 4.3 후속 작업

- 승인 데이터가 200건 넘으면 실제 재학습

### 4.4 관련 문서

- `training/lora/README.md` (재학습 루프)
