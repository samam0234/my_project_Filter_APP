# 영상 추적이 실제 검출기 잡음(중복 · 합쳐짐)에 대상을 놓치던 문제 — YOLO 91.4→99.4% / `19d000b73346792722c8a300b5063dc794250dea`

> 브랜치: `feature/tracking-hard`  
> 작성일: `2026-10-09 15:36`  
> 작성자: `agent`  
> 파일명: `261009_1536_19d000b_tracking-hard_feature-tracking-hard.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(video): 영상 추적이 실제 검출기 잡음(중복 · 합쳐짐)에 대상을 놓치던 문제 — YOLO 91.4→99.4%` |
| **커밋 번호 (SHA)** | `19d000b73346792722c8a300b5063dc794250dea` |
| **짧은 SHA** | `19d000b` |
| **브랜치** | `feature/tracking-hard` |
| **부모 커밋** | `a47df2f` |

## 2. 주 커밋 내용

- `instance_tracker.py`: 중복 검출 무시 · 합쳐짐 감지 · 색 재식별 · 재선택 지연
- 평가 시나리오 turn · lookalike · pan, 검증 문서

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "영상 추적은 합성 영상 · 일정한 걸음만 쟀음, YOLO 에서 약 9% 실패" 보완.

### 3.2 변경 범위
- 수정: `backend/app/services/instance_tracker.py`, `tests/unit/test_instance_tracker.py`, `scripts/experiments/video_tracking_eval.py`, 문서
- 추가: `docs/vaildates/video-tracking-hard-20261009.md` · YOLO 원자료 4개

### 3.3 기술 포인트
- 실패 원인을 프레임 단위 로그로 확인 후 고침 (추측으로 고치지 않음)

### 3.4 의도적으로 하지 않은 것
- 학습형 재식별(ReID) 모델 — lookalike 는 생김새로 못 가름

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 436 통과
- [x] YOLO cross 91.4→99.4%, pan 96.7→100%

### 4.2 부작용 / 리스크
- 대상이 화면 밖으로 나가면 약 0.8초 동안 직전 마스크 유지

### 4.3 후속 작업
- 실제 영상(방향 전환 · 세 명 이상 겹침)으로 확인

### 4.4 관련 문서
- `docs/vaildates/video-tracking-hard-20261009.md`
