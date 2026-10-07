# 영상 결과를 H.264 mp4 로 되돌리고 큰 영상에서 블러가 안 보이던 문제 수정 / `8ae85281a404563b88ef876b2dcc74caf17e67ce`

> 브랜치: `feature/video-fixes`  
> 작성일: `2026-10-07 22:45`  
> 작성자: `agent`  
> 파일명: `261007_2245_8ae8528_video-mp4-blur-scale_feature-video-fixes.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(video): 영상 결과를 H.264 mp4 로 되돌리고 큰 영상에서 블러가 안 보이던 문제 수정` |
| **커밋 번호 (SHA)** | `8ae85281a404563b88ef876b2dcc74caf17e67ce` |
| **짧은 SHA** | `8ae8528` |
| **브랜치** | `feature/video-fixes` |
| **부모 커밋** | `b4be99c` |

## 2. 주 커밋 내용

- 영상 결과 기본 형식을 **H.264 mp4**(원본 오디오 aac 포함)로 되돌림 — 번들 ffmpeg(`imageio-ffmpeg`)로 MJPG 임시 avi 를 변환
- ffmpeg 없음·변환 실패 시 webm(VP8) → avi 순으로 폴백 (결과는 잃지 않음)
- **블러 강도를 프레임 크기에 비례해 보정** — 큰 영상에서 받은 파일에 블러가 안 보이던 문제 수정
- 응답에 해석된 효과·강도 추가 (`X-Cutnkeep-Effect` · `-Intensity`, JSON `effect` · `intensity`)
- 설정 `VIDEO_OUTPUT_FORMAT` 기본 mp4, 시스템 화면 `video.ffmpeg`, `requirements*.txt` 에 `imageio-ffmpeg==0.6.0`

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지적: ① 처리된 영상은 mp4 여야 하는데 왜 webm 이냐 ② 처리 후 재생이 안 된다 ③ 다운로드해서 보니 블러가 안 되어 있다.
이 커밋은 ①과 ③의 서버 쪽. ②는 다음 커밋(브라우저 보관·다시 처리).

### 3.2 변경 범위
- 수정: `backend/app/services/{video_processor,system_status}.py`, `backend/app/routers/video.py`, `backend/app/core/config.py`, `backend/app/main.py`,
  `requirements.txt`, `requirements.docker.txt`, `.env.example`, `tests/unit/{test_batch_api,test_phase2,test_console_system}.py`

### 3.3 기술 포인트
- **mp4 가 가능한 이유**: 앞서 "OpenCV 에 H.264 인코더가 없다"는 이유로 webm 을 골랐으나, OpenCV 가 아니라 ffmpeg 로 변환하면 된다.
  `imageio-ffmpeg` 는 libx264·aac 가 들어 있는 정적 ffmpeg 를 휠로 번들한다 (Windows 84MB, 시스템 ffmpeg 설치 불필요). 단 libx264 는 GPL — 배포 시 라이선스 고지 필요
- 변환: `-map 0:v:0 -map 1:a:0?`(원본 오디오가 있을 때만), `scale=trunc(iw/2)*2:trunc(ih/2)*2:out_range=tv`(홀수 크기·full range 대응), `-pix_fmt yuv420p -movflags +faststart -shortest`
- **블러가 안 보인 원인(재현·측정)**: 블러 커널이 픽셀 단위(기본 15). 사진은 긴 변 1280px 로 줄여 처리하지만 영상은 원본 해상도 그대로 → 3840폭 배경 선명도 6.8→5.4(사실상 변화 없음), 1920폭도 약함.
  긴 변 > 1280 이면 그 비율만큼 강도를 키움(최대 255). 보정 후 3840폭 6.8→1.8. 1280 이하는 보정 없음(사진과 동일)
- 응답 `intensity` 는 보정 전 요청 강도 — 화면에 "강도 15" 처럼 사용자가 쓴 값 그대로 보인다

### 3.4 의도적으로 하지 않은 것
- 사진(단일·배치)의 큰 이미지 블러 보정 — 사진은 파이프라인이 긴 변을 줄여 처리해 영향이 작음. 필요하면 별도 확인
- 프레임 수 상한(240) 때문에 긴 영상이 잘리는 문제 — 별도

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 278 통과 (신규: 폴백 2, 변환 실패 보존, 강도 보정, 큰 프레임 블러, mp4 응답 2)
- [x] 실제 모델로 mp4 생성: h264(High) + aac, 홀수 높이 프레임도 정상, 임시 파일 정리

### 4.2 부작용 / 리스크
- **Docker 이미지를 다시 빌드해야 mp4 가 나온다** (requirements.docker.txt 변경). 안 하면 webm 으로 폴백
- 이미지 크기 증가(ffmpeg 번들), libx264 GPL 고지

### 4.3 후속 작업
- 브라우저 보관·다시 처리 (다음 커밋)

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md` (Video), `docs/vaildates/ui-check-20261007-console.md`
