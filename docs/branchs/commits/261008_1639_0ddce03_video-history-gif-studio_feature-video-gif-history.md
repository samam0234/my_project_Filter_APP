# 회원 영상을 작업 기록에 남기고, 작업실에 GIF 카테고리(움직이는 GIF 처리) 추가 / `0ddce03018edb5b8e5f4966bab61889522893a90`

> 브랜치: `feature/video-gif-history`  
> 작성일: `2026-10-08 16:39`  
> 작성자: `agent`  
> 파일명: `261008_1639_0ddce03_video-history-gif-studio_feature-video-gif-history.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(media): 회원 영상을 작업 기록에 남기고, 작업실에 GIF 카테고리(움직이는 GIF 처리) 추가` |
| **커밋 번호 (SHA)** | `0ddce03018edb5b8e5f4966bab61889522893a90` |
| **짧은 SHA** | `0ddce03` |
| **브랜치** | `feature/video-gif-history` |
| **부모 커밋** | `f3bfa10` |

## 2. 주 커밋 내용

- `jobs.kind`(image|video|gif) 추가 — 회원 영상이 작업 기록에 남고 첫 프레임 썸네일 저장
- `/files/{id}/before·after·thumb` 가 종류별 경로를 쓰도록 일반화 (`routers/upload.job_file`), 운영 콘솔 파일 보기도 같은 규칙
- `POST /api/v1/gif` + `services/gif_processor.py` — 프레임마다 영상과 같은 규칙(`FrameRenderer` 공용화), 간격·반복 유지, 배경 제거는 투명 GIF
- 작업실 카테고리 탭(사진 · GIF, 영상 바로가기, `?type=gif`), 작업 기록 종류 필터·배지, 작업 상세 영상 재생
- nginx 영상·GIF 경로 업로드 85MB · 대기 600초

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청: "영상도 작업 기록으로 남겨야" · "작업실에서 GIF 도 처리할 수 있도록 카테고리와 기능". 회원 영상은 파일(owner.json)로만 보관돼 작업 기록에 보이지 않았다.

### 3.2 변경 범위
- 추가: `backend/app/routers/gif.py`, `backend/app/services/gif_processor.py`, `frontend/src/components/gif/GifWorkspace.tsx`(+테스트), `frontend/src/components/common/Step.tsx`, `frontend/src/pages/HistoryPage.test.tsx`, `tests/unit/test_media_history.py`
- 수정: 모델·세션 마이그레이션·저장소·스키마·라우터(upload · jobs · video · console · router), `video_processor.py`(FrameRenderer), 프론트 작업실·기록·상세·영상·카드·뷰어·타입·클라이언트, 콘솔 작업 표, nginx, API 문서, `.env.example`, 가이드

### 3.3 기술 포인트
- 기존 DB 는 `_ADDED_COLUMNS` 로 기동 시 `ALTER TABLE jobs ADD COLUMN kind` (Docker DB 적용 로그 확인), 예전 행은 NULL → image
- 영상 보관 위치(`uploads/videos/{id}`)와 owner.json 은 그대로 두어 기존 `GET /video/{id}` · 회원 삭제(owner.json 기준)와 호환
- GIF 투명은 1비트 — 255색으로 줄이고 255번을 투명색으로, `disposal=2` 로 이전 프레임 잔상 방지
- 비로그인 GIF 는 사진처럼 data URL 응답(디스크·DB 에 남기지 않음)
- 파일 경로는 업로드 폴더 안인지 확인 후 제공

### 3.4 의도적으로 하지 않은 것
- 영상·GIF 품질 점수(검증 단계 없음 → 0, 화면에서 숨김), 비로그인 영상의 작업 기록(저장하지 않는 정책 유지), 영상 원본이 avi·mkv 일 때 재생 변환(안내만)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 387 · 프론트 vitest 49 · 콘솔 vitest 21 · 빌드 통과
- [x] Docker 재빌드 후 비로그인 GIF 탭 실제 처리: 10프레임 약 4초(모델 준비 후), 프레임 수·간격(90ms)·반복 유지, 배경 95% 투명
- [x] 작업 기록·상세 화면(가짜 API 응답) — 영상 실제 mp4 재생(readyState 4), 종류 배지·필터

### 4.2 부작용 / 리스크
- 영상 원본이 avi·mkv 면 브라우저가 원본을 재생하지 못함 (결과 mp4 는 재생됨)
- GIF 프레임이 많으면 처리 시간이 프레임 수에 비례 (상한 120)

### 4.3 후속 작업
- 실제 회원 계정으로 영상·GIF 작업 기록 브라우저 확인 (테스트 계정 정리 권한 필요)

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md` (Video · GIF · 결과 파일 · Jobs)
