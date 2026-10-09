# 영상 · GIF 에서 "왼쪽 사람"처럼 고른 대상을 프레임 사이로 따라가기 / `a75590925589fa8724664b0b09ee448b5671e754`

> 브랜치: `feature/video-tracking`  
> 작성일: `2026-10-09 09:49`  
> 작성자: `agent`  
> 파일명: `261009_0949_a755909_video-tracking_feature-video-tracking.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(video): 영상 · GIF 에서 "왼쪽 사람"처럼 고른 대상을 프레임 사이로 따라가기` |
| **커밋 번호 (SHA)** | `a75590925589fa8724664b0b09ee448b5671e754` |
| **짧은 SHA** | `a755909` |
| **브랜치** | `feature/video-tracking` |
| **부모 커밋** | `7acf8b6` |

## 2. 주 커밋 내용

- `services/instance_tracker.py` 신설: 고른 대상 + 다른 사람 다중 추적 (예측 IoU · 색 분포 · 일부 가려짐 · 재획득)
- `FrameRenderer` 가 위치 · 순서 · 개수 selector 일 때 추적기 사용, 설정 `VIDEO_TRACK_INSTANCES`
- 평가 `scripts/experiments/video_tracking_eval.py` (정답 세그 · YOLO)

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "영상 프레임 간 추적: 사람이 겹치면 고른 대상이 바뀔 수 있음" 개선.

### 3.2 변경 범위
- 추가: `instance_tracker.py`, `tests/unit/test_instance_tracker.py`, 평가 스크립트, `docs/vaildates/video-tracking-20261009.md` · 원자료 2개
- 수정: `video_processor.py`, `config.py`, `.env.example`, API · FEATURES · user-frontend · LOGIC_STRUCTURE · backend README · vaildates 색인

### 3.3 기술 포인트
- 위치만 쓰면 교차 때 앞사람으로 넘어감 → 다른 사람도 추적해 앞사람은 자기 추적이 가져가게
- 가려지는 동안 조각 무게중심으로 속도가 무너짐 → 일부만 보이면 예측 위치 유지

### 3.4 의도적으로 하지 않은 것
- 학습형 재식별(ReID) 모델 — 의존성 · 속도 부담, 실제 영상 평가 데이터 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 427 · 프론트 54 통과
- [x] 지나간 뒤 대상 유지 0% → 98.9%(정답 세그) · 0.9% → 91.4%(YOLO)

### 4.2 부작용 / 리스크
- "왼쪽"을 첫 프레임 기준으로 해석 (원하지 않으면 VIDEO_TRACK_INSTANCES=false)

### 4.3 후속 작업
- LoRA 개선, YOLO 재학습 파이프라인

### 4.4 관련 문서
- `docs/vaildates/video-tracking-20261009.md`
