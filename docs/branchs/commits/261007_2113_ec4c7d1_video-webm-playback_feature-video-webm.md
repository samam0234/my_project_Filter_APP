# 결과를 브라우저에서 바로 재생되는 webm 으로 바꾸고 화면에서 재생 / `ec4c7d17ee01e94cff7e8a66fd5307f1971ee679`

> 브랜치: `feature/video-webm`  
> 작성일: `2026-10-07 21:13`  
> 작성자: `agent`  
> 파일명: `261007_2113_ec4c7d1_video-webm-playback_feature-video-webm.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(video): 결과를 브라우저에서 바로 재생되는 webm 으로 바꾸고 화면에서 재생` |
| **커밋 번호 (SHA)** | `ec4c7d17ee01e94cff7e8a66fd5307f1971ee679` |
| **짧은 SHA** | `ec4c7d1` |
| **브랜치** | `feature/video-webm` |
| **부모 커밋** | `5cf7d67` |

## 2. 주 커밋 내용

- 영상 출력 기본값 webm(VP8) — 브라우저 `<video>` 로 바로 재생
- VP8 인코더를 못 열면 MJPG avi 로 자동 전환, `format` / `X-Cutnkeep-Format` 으로 구분
- 설정 `VIDEO_OUTPUT_FORMAT` (webm | avi), 보관본 조회는 `result.webm` · 예전 `result.avi` 모두
- 프론트 영상 페이지: 결과 바로 재생, 회원 보관본은 `fetchBlob`(쿠키 포함)으로 받아 재생·저장
- CORS 노출 헤더에 `X-Cutnkeep-Format`

## 3. 상세 내용

### 3.1 배경 / 목적
결과가 MJPG avi 라 "내려받아 플레이어로 열어 주세요" 안내가 필요했다 (`39b1093` 의 의도적으로 하지 않은 것).

### 3.2 변경 범위
- 수정: `backend/app/services/video_processor.py`, `backend/app/routers/video.py`, `backend/app/core/config.py`, `backend/app/main.py`,
  `frontend/src/{pages/VideoPage.tsx, pages/VideoPage.test.tsx, api/client.ts, api/client.test.ts, types/index.ts}`,
  `tests/unit/{test_batch_api,test_phase2}.py`, `docs/API_DOCUMENTATION.md`, `docs/guidance/user-frontend.md`, `.env.example`

### 3.3 기술 포인트
- 코덱 조사(Windows · opencv 4.11/4.13): `avc1`/`H264` 는 열리지만 OpenH264 DLL 이 없어 실제 H.264 가 아님 → mp4 제외. VP8 · VP9 webm 은 동작
- 인코딩 속도(720p 노이즈, 최악 조건): MJPG 56fps · VP8 13fps · VP9 5fps → VP8 선택
- 실제 모델 45프레임: avi 29.1s · webm 30.2s (병목은 세그, 인코딩 비용 약 4%). 크기 1700KB → 1135KB
- `<video>` 에 쿠키가 다른 도메인으로 안 가는 배포를 고려해 URL 직접 대신 Blob → object URL (언마운트 시 해제)
- ffmpeg 로그 "tag VP80 is not supported with codec id 139" 는 태그 매핑 경고일 뿐 VP8 로 정상 기록됨 (EBML 헤더·재읽기 확인)

### 3.4 의도적으로 하지 않은 것
- H.264 mp4 (OpenH264 라이선스·배포 부담), 프레임 간 추적

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과, 프론트 vitest 32 · tsc · build 통과
- [x] 실제 모델로 webm 생성 → OpenCV 재읽기 45/45 프레임

### 4.2 부작용 / 리스크
- Docker 이미지의 opencv 휠도 VP8 포함(pip 휠 공통) — 못 열면 avi 로 내려가므로 기능은 유지

### 4.3 후속 작업
- 실브라우저 재생 확인은 마지막 UI 점검에서

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md` (Video)
