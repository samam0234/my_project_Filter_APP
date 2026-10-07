# 브라우저가 보내는 MIME 으로 avi 가 거절되던 문제와 테스트 업로드 폴더 오염 수정 / `f04c1a8a7babfe6f1845540e891e74e10151d216`

> 브랜치: `feature/batch-video-ui`  
> 작성일: `2026-10-07 12:10`  
> 작성자: `agent`  
> 파일명: `261007_1200_f04c1a8_video-mime-test-pollution_feature-batch-video-ui.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(video): 브라우저가 보내는 MIME 으로 avi 가 거절되던 문제와 테스트 업로드 폴더 오염 수정` |
| **커밋 번호 (SHA)** | `f04c1a8a7babfe6f1845540e891e74e10151d216` |
| **짧은 SHA** | `f04c1a8` |
| **브랜치** | `feature/batch-video-ui` |
| **부모 커밋** | `39b1093` |

## 2. 주 커밋 내용

- 영상 MIME 검사 완화(`video/*` 또는 `application/octet-stream`)
- 대신 파일 앞부분 시그니처로 검증(`validate_video_signature`: AVI · MP4/MOV · WebM/MKV)
- 테스트 conftest 가 `upload_dir` 도 임시 폴더로 돌리도록 수정
- 테스트: MIME 변형(video/avi, x-msvideo, octet-stream), 시그니처 거절

## 3. 상세 내용

### 3.1 배경 / 목적
실브라우저(Playwright) 점검에서 모든 `.avi` 업로드가 400("영상 MIME 이 아닙니다")으로 거절됐다.
브라우저는 `.avi` 를 `video/avi` 로 보내는데 서버 허용 목록이 이를 몰랐다. MIME 은 클라이언트가 정하는 값이므로 목록을 늘리기보다 내용 시그니처로 판단하는 편이 정확하다.
또한 배치 API 테스트가 실제 `backend/data/uploads/batches` 에 폴더 4개(인수인계 시 실행분 포함)를 남기고 있었다.

### 3.2 변경 범위
- 수정: `backend/app/routers/video.py`, `backend/app/core/security.py`, `tests/unit/conftest.py`, `tests/unit/test_batch_api.py`
- 정리: 오염된 `batches` 폴더·점검 중 남은 고아 배치 행 삭제

### 3.3 기술 포인트
- `_mime_ok` 는 MIME 이 "영상 계열이거나 알 수 없음"일 때만 통과, 최종 판단은 시그니처
- `api_env` fixture 가 `get_settings().upload_dir` 를 tmp_path 로 monkeypatch

### 3.4 의도적으로 하지 않은 것
- 영상 코덱 검증(디코딩 가능 여부)은 처리 단계에서 확인

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 단위 테스트 통과, 실브라우저 재점검에서 avi 업로드 성공
- [x] 테스트 후 실제 uploads 폴더에 찌꺼기 없음 확인

### 4.2 부작용 / 리스크
- 시그니처는 컨테이너 첫 바이트만 본다(손상된 본문은 처리 단계에서 실패 처리)

### 4.3 후속 작업
- `feature/celery-worker` 의 Celery 실가동 점검

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md`, `docs/vaildates/ui-check-20261007.md`
