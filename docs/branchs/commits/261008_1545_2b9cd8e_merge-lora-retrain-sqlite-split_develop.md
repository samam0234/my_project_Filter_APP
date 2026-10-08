# LoRA 재학습 · 서비스 DB 파일 분리 2개 브랜치 총 병합 / `2b9cd8e`

> 브랜치: `develop`  
> 작성일: `2026-10-08 15:46`  
> 작성자: `agent`  
> 파일명: `261008_1545_2b9cd8e_merge-lora-retrain-sqlite-split_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge(develop): LoRA 재학습 · 서비스 DB 파일 분리 2개 브랜치 총 병합` |
| **병합 커밋 (쌓인 순서)** | `c7b6e4b` lora-retrain → `2b9cd8e` sqlite-host-docker-split |
| **브랜치** | `develop` (`git merge --no-ff`, 사용자 지시 "남은 일 처리 → 커밋 후 최종 병합"에 따라 마지막에 한 번) |
| **병합 전 develop** | `ad27964` |

## 2. 주 커밋 내용

| 브랜치 | 커밋 | 내용 |
|--------|------|------|
| `feature/lora-retrain` | `d3d9b77` · `cb9d2f1` | 재학습 판정에 처음 본 30문장 추가, 방해물 문장 시드로 재학습(방해물 78.7→95.7%, 홀드아웃 70.0→87.5%, 처음 본 문장 70.0→73.3%) → 판정 통과해 배포본 교체 |
| `feature/sqlite-host-docker-split` | `8eb1d74` | 호스트(`cutnkeep.host.db`)·Docker(`cutnkeep.db`) 서비스 SQLite 분리, 기동 시 `quick_check` 손상 감지, 복구 절차 문서 |

## 3. 상세 내용

### 3.1 배경 / 목적
직전 보고의 "남은 일": LoRA 재학습, 어려운 사례 수집 여부 결정, 호스트·Docker DB 분리, 병합, push.

### 3.2 변경 범위
각 브랜치 커밋 기록 참조.

### 3.3 기술 포인트
- 충돌 없음 (`sqlite-host-docker-split` 은 `d3d9b77` 위에서 갈라졌고 `cb9d2f1` 과 겹치는 파일 없음)
- 어려운 사례 수집(`HARD_EXAMPLE_CONF`)은 **기본 꺼짐 유지로 결정** — 켜면 회원 이미지가 더 저장되므로 개인정보 안내·보관 기간을 정한 뒤 켠다 (`docs/guidance/learning-loop.md` ⑥)
- 기본 LLM 은 ollama + 해석 체인 유지 (LoRA 는 처음 본 문장 73.3% 로 체인 96.7% 보다 낮음)

### 3.4 의도적으로 하지 않은 것
- main 병합 · 배포

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 병합 후 백엔드 pytest 375 passed
- [x] Docker backend 재빌드: `SQLITE_PATH=data/cutnkeep.db`, 손상 경고 없음
- [x] LoRA 재학습·평가 정상 종료, 판정 채택

### 4.2 부작용 / 리스크
- 로컬 `.env`(git 무시)의 `SQLITE_PATH` 를 `data/cutnkeep.host.db` 로 바꿈 — 호스트 backend 는 빈 DB 로 시작
- 이전 LoRA 는 `backend/models/lora_prev_261008_1543` (되돌리기는 검증 문서 참고)

### 4.3 후속 작업
- 승인 문장이 쌓이면 LoRA 재학습, 서비스 DB 를 배포에서 MariaDB 로 옮길지 검토

### 4.4 관련 문서
- `docs/vaildates/lora-retrain-20261008.md`, `docs/plan/DATABASE.md`
