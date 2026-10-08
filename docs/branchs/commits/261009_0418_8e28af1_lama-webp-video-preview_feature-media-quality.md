# 대상 지우기를 LaMa 인페인팅으로, GIF 배경 제거에 부드러운 경계 WebP, 영상 원본 미리 보기 mp4 / `8e28af1658205b34bb12b9e95fb2466aa97ec723`

> 브랜치: `feature/media-quality`  
> 작성일: `2026-10-09 04:18`  
> 작성자: `agent`  
> 파일명: `261009_0418_8e28af1_lama-webp-video-preview_feature-media-quality.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(quality): 대상 지우기를 LaMa 인페인팅으로, GIF 배경 제거에 부드러운 경계 WebP, 영상 원본 미리 보기 mp4` |
| **커밋 번호 (SHA)** | `8e28af1658205b34bb12b9e95fb2466aa97ec723` |
| **짧은 SHA** | `8e28af1` |
| **브랜치** | `feature/media-quality` |
| **부모 커밋** | `16dd40a` |

## 2. 주 커밋 내용

- 대상 지우기 빈자리 메우기: OpenCV Telea → 학습형 **LaMa**(ONNX, Apache-2.0, `services/inpaint.py`), `INPAINT_ENGINE=auto`(모델 없으면 Telea), 영상·GIF 는 Telea 유지
- GIF 배경 제거: 같은 프레임의 **움직이는 WebP**(8비트 알파, 반투명 경계)도 생성 → "WebP 저장"
- 영상 원본이 avi·mkv·mov 면 작업 기록에서 재생되는 mp4 미리 보기(`original.mp4`)
- 파일 응답 MIME 을 확장자로 직접 지정 (Windows 의 `.webp` → text/plain + nosniff 로 이미지 안 보이던 문제)
- 콘솔 시스템 화면에 메우기 엔진, 평가 스크립트 `scripts/experiments/inpaint_eval.py` · 문서 `docs/vaildates/inpaint-20261009.md`

## 3. 상세 내용

### 3.1 배경 / 목적
품질 개선 요청. 사용자 가이드에 한계로 적혀 있던 "큰 물체를 지우면 번진 자국"과 "GIF 경계가 거칠다", "avi 원본은 작업 기록에서 재생 안 됨"을 해결.

### 3.2 변경 범위
- 추가: `backend/app/services/inpaint.py`, `scripts/experiments/inpaint_eval.py`, 검증 문서·원자료·비교 이미지 2장
- 수정: `effects.py` · `gif_processor.py` · `video_processor.py` · 라우터(gif · upload · jobs · video · console) · 스키마 · `system_status.py` · 설정, 프론트(GIF 작업 화면 · 결과 뷰어 · 작업 상세 · 가이드 · 타입), 콘솔(시스템 화면 · 타입), 문서(API · models README · .env.example)
- git 밖: `backend/models/lama_fp32.onnx`(208MB, README 에 받는 법)

### 3.3 기술 포인트
- LaMa 는 512×512 고정 입력 → 마스크 상자 + 60% 여유로 잘라 넣고 마스크 영역만 합성 (나머지 픽셀은 원본)
- 평가: 정답이 있는 구멍(배경 위에 사람 모양 구멍) 60장 — L1 20.2→15.6, PSNR +2.6dB, 무늬(경사) 오차 −26%, LaMa 가 나은 비율 83%/98%, 95% 구간 모두 0 미포함. 사진당 CPU +1.3초

### 3.4 의도적으로 하지 않은 것
- 영상·GIF 의 LaMa (프레임 수 × 1.3초), YOLO 재학습(데이터 필요)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 405 · 프론트 50 · 콘솔 21 · 빌드 통과
- [x] Docker 실제 회원 흐름: 사진 "오른쪽 사람 지워줘"(LaMa, 첫 요청 19초) · GIF(WebP `image/webp`) · avi 영상(원본 mp4 미리 보기 재생 readyState 4) · 작업 기록 사진1·영상1·GIF1 · CSP 위반·오류 0건

### 4.2 부작용 / 리스크
- LaMa 모델 파일이 없으면 Telea 로 동작 (배포 시 모델 받기 필요)
- 큰 구멍(≥15%) 표본 2장 — 화면 대부분을 지우는 경우는 여전히 어색할 수 있음

### 4.3 후속 작업
- GPU onnxruntime 으로 LaMa 시간 단축(선택)

### 4.4 관련 문서
- `docs/vaildates/inpaint-20261009.md`, `docs/API_DOCUMENTATION.md`
