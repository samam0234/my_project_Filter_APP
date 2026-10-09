# 세그 실패 사진 라벨링 묶음(초벌 라벨 · Label Studio · 검사), 섞임 평가 표본 확대 / `ca1820833007f7fea2f197a7f058f896e5375003`

> 브랜치: `feature/seg-labeling`  
> 작성일: `2026-10-09 16:49`  
> 작성자: `agent`  
> 파일명: `261009_1649_ca18208_seg-labeling_feature-seg-labeling.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(seg): 세그 실패 사진 라벨링 묶음(초벌 라벨 · Label Studio · 검사), 섞임 평가 표본 확대` |
| **커밋 번호 (SHA)** | `ca1820833007f7fea2f197a7f058f896e5375003` |
| **짧은 SHA** | `ca18208` |
| **브랜치** | `feature/seg-labeling` |
| **부모 커밋** | `40926af` |

## 2. 주 커밋 내용

- `scripts/seg_labeling.py` (export · check)
- `leak_eval.py --download-touching`, 판정 표본 150장, 기준 수치 문서

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "세그 정확도는 실제 실패 사진에 라벨을 달아야 개선" · "평가 표본이 작음" 을 실행 가능한 도구로.

### 3.2 변경 범위
- 추가: `scripts/seg_labeling.py`, `tests/unit/test_seg_labeling.py`, `docs/vaildates/leak-baseline-20261009.md` · 원자료
- 수정: `scripts/experiments/leak_eval.py`, `scripts/retrain_yolo.py`, learning-loop · yolo-retrain · FEATURES · scripts README · 색인

### 3.3 기술 포인트
- 초벌 라벨은 큰 모델(yolo26x)로 — 사람은 고치기만
- 회원 사진: 출력은 git 밖, 외부 라벨링 서비스 금지 안내

### 3.4 의도적으로 하지 않은 것
- HARD_EXAMPLE_CONF 켜기 (개인정보 결정은 운영자 몫)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 440 통과
- [x] 실제 피드백 4장으로 export · check 시험 (시험 폴더는 삭제)

### 4.2 부작용 / 리스크
- 평가 사진이 늘어 예전 n=48 수치와 다른 사진이 뽑힘 (문서화)

### 4.3 후속 작업
- 실패 사진 수백 장 라벨 후 retrain_yolo --extra

### 4.4 관련 문서
- `docs/vaildates/leak-baseline-20261009.md`
