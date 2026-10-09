# 카메라가 움직이는 영상도 프레임을 맞춰 배경판으로 지우기 — 팬 L1 27.5→6.9 / `d17bef62c98dcf0a58b25e7f4ac23c6b8ee3d408`

> 브랜치: `feature/video-removal-pan`  
> 작성일: `2026-10-09 15:09`  
> 작성자: `agent`  
> 파일명: `261009_1509_d17bef6_video-removal-pan_feature-video-removal-pan.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(video): 카메라가 움직이는 영상도 프레임을 맞춰 배경판으로 지우기 — 팬 L1 27.5→6.9` |
| **커밋 번호 (SHA)** | `d17bef62c98dcf0a58b25e7f4ac23c6b8ee3d408` |
| **짧은 SHA** | `d17bef6` |
| **브랜치** | `feature/video-removal-pan` |
| **부모 커밋** | `12084de` |

## 2. 주 커밋 내용

- `video_inpaint.py` aligned 방식 (프레임 맞추기 · 캔버스 배경판)
- 판정 규칙(시차 거부 · 느린 이동 보정), 응답 `removal.mode`
- 평가 zoom 시나리오, 검증 문서

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "카메라가 움직이는 영상은 지우기가 예전 방식" 개선.

### 3.2 변경 범위
- 수정: `backend/app/services/video_inpaint.py`, `video_processor.py`, `tests/unit/test_video_inpaint.py`, `scripts/experiments/video_removal_eval.py`, API · FEATURES · 검증 문서
- 추가: `docs/vaildates/video-removal-pan-20261009.md` · 원자료

### 3.3 기술 포인트
- 맞춘 뒤 남는 차이로 시차를 걸러 잘못 맞춘 배경판을 쓰지 않음

### 3.4 의도적으로 하지 않은 것
- 시차 큰 장면용 광학 흐름 기반 채우기 (비용 · 품질 불확실)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 통과
- [x] 팬 L1 27.5→6.9, 확대 26.1→9.0

### 4.2 부작용 / 리스크
- 카메라 이동 영상 처리 시간 증가 (1080p 1단계 +140ms/프레임)

### 4.3 후속 작업
- 실제 손떨림 영상으로 확인

### 4.4 관련 문서
- `docs/vaildates/video-removal-pan-20261009.md`
