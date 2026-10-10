# 영상 · GIF 대상 지우기를 다른 프레임에서 보인 배경판으로 메우기, LaMa 입력 테두리 누수 수정 / `ec75c5f822ca77278ce5526944b6780e22ef53bd`

> 브랜치: `feature/video-removal-propagate`  
> 작성일: `2026-10-09 09:19`  
> 작성자: `agent`  
> 파일명: `261009_0919_ec75c5f_video-removal-propagate_feature-video-removal-propagate.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(video): 영상 · GIF 대상 지우기를 다른 프레임에서 보인 배경판으로 메우기, LaMa 입력 테두리 누수 수정` |
| **커밋 번호 (SHA)** | `ec75c5f822ca77278ce5526944b6780e22ef53bd` |
| **짧은 SHA** | `ec75c5f` |
| **브랜치** | `feature/video-removal-propagate` |
| **부모 커밋** | `362c28d` |

## 2. 주 커밋 내용

- `services/video_inpaint.py` — 배경판(다른 프레임에서 보인 배경)으로 영상 · GIF 지우기, 안 보인 곳만 LaMa 한 번
- 카메라 고정 판정 → 움직이면 예전 방식(프레임마다 Telea) 자동
- `services/inpaint.py` — LaMa 입력 구멍을 넓혀 비움 (테두리 누수 수정)
- 평가 `scripts/experiments/video_removal_eval.py` · 문서 · 사진 평가 재측정

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "영상·GIF 의 큰 물체 지우기 개선". 프레임마다 Telea 는 번지고 깜빡였다.

### 3.2 변경 범위
- 추가: `video_inpaint.py`, `video_removal_eval.py`, `tests/unit/test_video_inpaint.py`, 검증 문서 · 원자료 · 비교 이미지
- 수정: `video_processor.py`(두 번 읽기), `gif_processor.py`, `inpaint.py`, `config.py`(VIDEO_REMOVE_MODE · 경고), 라우터 2개, 문서 · 가이드

### 3.3 기술 포인트
- 마스크는 비트 압축 보관, 배경 누적은 합 · 개수, 판정은 마스크 밖 축소 회색조 밝기 차의 중앙값 · 90 백분위수
- 실험 중 LaMa 입력 문제 발견: 구멍 안 · 테두리 색을 참고 → 검정 구멍이면 어둡게 물듦. 모델 해상도에서 5px 넓혀 비워 넣도록 고침
- 사진 수치는 테두리 누수가 있던 상태였어서 다시 재고 문서를 정정 (결론 동일)

### 3.4 의도적으로 하지 않은 것
- 흔들리는 카메라의 영상 정합 후 배경판, 그림자 지우기

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 422 통과
- [x] 합성 영상 60개: 움직이는 대상 L1 26.4→0 · 깜빡임 22.5→0, 제자리 27.3→23.8, 카메라 이동 동일

### 4.2 부작용 / 리스크
- 합성 영상은 배경이 완전히 고정이라 실제보다 좋게 나온다 (문서에 명시)
- 영상을 두 번 읽음 (메모리 1080p 240프레임 약 85MB)

### 4.3 후속 작업
- GIF 경계, 영상 추적, LoRA, YOLO 재학습 파이프라인

### 4.4 관련 문서
- `docs/vaildates/video-removal-20261009.md`, `docs/vaildates/inpaint-20261009.md`
