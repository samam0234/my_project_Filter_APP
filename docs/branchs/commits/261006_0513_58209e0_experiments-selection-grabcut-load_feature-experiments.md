# 실험 기반 인스턴스 선택·GrabCut 개선과 실험 스크립트 / `58209e0c0be90b280bf9efdf1273ae76b194620a`

> 브랜치: `feature/experiments`  
> 작성일: `2026-10-06 05:13`  
> 작성자: `agent`  
> 파일명: `261006_0513_58209e0_experiments-selection-grabcut-load_feature-experiments.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `perf(vision): 실험 기반 인스턴스 선택·GrabCut 개선과 실험 스크립트` |
| **커밋 번호 (SHA)** | `58209e0c0be90b280bf9efdf1273ae76b194620a` |
| **짧은 SHA** | `58209e0` |
| **브랜치** | `feature/experiments` |
| **부모 커밋** | `018dc07` (feature/prompt-learning) |

## 2. 주 커밋 내용

- 실험 스크립트 3개 (`scripts/experiments/`) + 결과 문서·원자료
- 인스턴스 선택: 작은 배경 인스턴스 제외 → 64.0% → 71.6%
- GrabCut ROI → 정제 3배 빠름, 단건 지연 7.4 → 6.2 s

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 점검 5번 "검증의 한계"를 직접 실험 (사용자 요청 "5번은 직접 실험해보고").
확장 평가셋(56건)은 `feature/prompt-learning` 에서 이미 반영.

### 3.2 변경 범위

- 추가: `scripts/experiments/{selection_e2e,refine_speed,load_test}.py`,
  `docs/vaildates/{experiments-20261006.md, selection_e2e_20261006.json, load_test_20261006*.json}`
- 수정: `backend/app/services/{instance_selector,effects}.py`, `tests/unit/test_instance_selector.py`,
  `docs/{WORKFLOW.md, vaildates/README.md}`, `scripts/README.md`

### 3.3 기술 포인트

- 선택 실험은 LLM 을 빼고 정답 selector 로 세그+선택 규칙만 측정, 정답은 라벨 폴리곤에 같은 정렬 규칙
- 작은 인스턴스 기준은 0.05~0.3 비교 후 0.2 (상대) + 1% (절대 OR). 정답 정의와 같은 절대 1% 만 쓰면 74.2% 지만 실험에 맞춘 값이라 택하지 않음
- GrabCut 결과는 원 마스크 주변 띠로 잘리므로 ROI 밖 계산은 낭비 → ROI + 긴 변 800 상한
- 부하 실험 대기 조건이 cp949 로그를 UTF-8 로 grep 해 멈춘 문제 → 직접 실행으로 해결 (실험 스크립트와 무관)

### 3.4 의도적으로 하지 않은 것

- GrabCut 제거 — 정답 대비 IoU 개선은 없었지만 COCO 폴리곤이 거칠어 세밀한 경계 판단 불가, 눈 비교 후 결정
- Ollama 병렬화·해석 캐시 (배포 환경 결정 후)
- 맨 앞/맨 뒤 측정 (깊이 정답 없음)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| 인스턴스 선택 (명확 1320문항) | 64.0% | **71.6%** |
| GrabCut 정제 중앙값 | 690 ms | **216 ms** (정답 IoU 0.746 → 0.750) |
| effect_applier | 2.09 s | **1.04 s** |
| 단건 p50 / 처리량 | 7.4 s / 7.3 건/분 | **6.2 s / 9.6 건/분** |
| 동시 8 | 오류 0, `/health` 최대 12 ms, 처리량 약 21 건/분 (LLM 병목) | — |

- [x] pytest 전체 통과 (신규 1건)

### 4.2 부작용 / 리스크

- 군중 사진에서 큰 사람 1명 + 작은 사람 여럿이면 작은 사람들은 위치 비교에서 빠짐 (모두 작으면 그대로)
- ROI GrabCut 은 배경 색 모델이 주변부만 보므로 전체 대비 결과가 약간 다름 (IoU 중앙값 0.976)

### 4.3 후속 작업

- 6번 보안·운영 점검 + 2번 프론트 테스트·CI
- 세그 검출 재현율 83% → YOLO 재학습/큰 모델 비교

### 4.4 관련 문서

- `docs/vaildates/experiments-20261006.md`
