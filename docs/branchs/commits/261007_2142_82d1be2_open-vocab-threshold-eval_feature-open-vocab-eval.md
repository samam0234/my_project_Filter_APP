# 오픈 보캐브 임계값 측정과 헬멧 판정 정정 / `82d1be2021f0939769ef45e214491700e39ea4a0`

> 브랜치: `feature/open-vocab-eval`  
> 작성일: `2026-10-07 21:42`  
> 작성자: `agent`  
> 파일명: `261007_2142_82d1be2_open-vocab-threshold-eval_feature-open-vocab-eval.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(vaildates): 오픈 보캐브 임계값 측정과 헬멧 판정 정정` |
| **커밋 번호 (SHA)** | `82d1be2021f0939769ef45e214491700e39ea4a0` |
| **짧은 SHA** | `82d1be2` |
| **브랜치** | `feature/open-vocab-eval` |
| **부모 커밋** | `2385c6a` |

## 2. 주 커밋 내용

- `docs/vaildates/open-vocab-20261007.md` 2절 추가: 임계값 측정(전체·클래스별), 실제 사진 재확인, 워밍업 실측, 운영 메모
- **정정**: `2d7cab9` 의 "헬멧이 없을 가능성이 높다 → 오검출 가능" 은 틀렸다 — 사진 속 선수가 빨간 타격 헬멧을 쓰고 있다
- 재현 스크립트 `scripts/experiments/dino_threshold.py`, 요약 `docs/vaildates/open_vocab_threshold_20261007.json`
- `docs/vaildates/README.md` 목록 갱신

## 3. 상세 내용

### 3.1 배경 / 목적
`15e2eed` 에서 DINO 임계값을 0.35 로 분리하면서 "COCO 정답 기반 측정은 후속 문서 커밋" 으로 남겼다. 그 측정과, 그 과정에서 드러난 판단 오류를 기록한다.

### 3.2 변경 범위
- 추가: `scripts/experiments/dino_threshold.py`, `docs/vaildates/open_vocab_threshold_20261007.json`
- 수정: `docs/vaildates/open-vocab-20261007.md`, `docs/vaildates/README.md`

### 3.3 기술 포인트
- 측정: COCO val2017 300장 × 10클래스 = 3,000쌍(있음 565 · 없음 2,435), 원본 주석 `instances_val2017.json`
- 결과: 0.25 → 0.35 에서 오검출률 17.9% → 7.4%, 재현율 96.8% → 92.9%, 정밀도 0.556 → 0.746. 0.40 부터 재현율 급락(87.4%)
- 첫 측정은 프로젝트 4클래스로 재매핑된 `coco_val_sel/labels` 를 정답으로 써서 사람 외 클래스가 모두 "없음" 이 되는 잘못이 있었다 → 버리고 다시 측정. 스크립트 docstring 에 경고로 남김
- 커밋한 스크립트로 다시 돌려 같은 수치가 나오는 것을 확인
- 실제 사진(000000000872): helmet 2개 → 1개(정답, 점수 0.70, 빠진 1개는 라벨이 빈 박스), shirt 는 점수 0.31 로 놓침(임계값의 대가)

### 3.4 의도적으로 하지 않은 것
- 기본값 재조정 — 측정 결과 0.35 가 균형점이라 유지
- COCO 밖 정답 데이터셋(LVIS 등) 측정 — 지금 수치는 COCO 클래스로 잰 대리 지표

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 측정 2회(임시 스크립트 · 커밋한 스크립트) 동일 수치

### 4.2 부작용 / 리스크
- `15e2eed` 커밋 본문의 "헬멧이 없는 사진에 헬멧 2개" 는 사실과 다르다 (커밋은 이미 기록돼 고치지 않고 이 문서·기록에서 정정)

### 4.3 후속 작업
- 옷 계열(shirt)처럼 점수가 낮게 나오는 대상은 LLM 이 더 구체적인 문구(white shirt 등)를 만들면 나아지는지 확인

### 4.4 관련 문서
- `docs/vaildates/open-vocab-20261007.md`
