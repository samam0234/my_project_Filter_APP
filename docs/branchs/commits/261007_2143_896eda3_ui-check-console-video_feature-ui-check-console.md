# 브라우저 확인에 영상 재생·콘솔 관리자 로그인·회원 삭제·시스템 흐름 추가 / `896eda39e74022478919a5e0fe2f4ab22d09af86`

> 브랜치: `feature/ui-check-console`  
> 작성일: `2026-10-07 21:43`  
> 작성자: `agent`  
> 파일명: `261007_2143_896eda3_ui-check-console-video_feature-ui-check-console.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `test(ui): 브라우저 확인에 영상 재생·콘솔 관리자 로그인·회원 삭제·시스템 흐름 추가` |
| **커밋 번호 (SHA)** | `896eda39e74022478919a5e0fe2f4ab22d09af86` |
| **짧은 SHA** | `896eda3` |
| **브랜치** | `feature/ui-check-console` |
| **부모 커밋** | `13636e7` |

## 2. 주 커밋 내용

- `scripts/experiments/ui_check.py`: 영상 재생 확인(`assert_video_plays`), webm 받기, 콘솔 로그인·회원 삭제·시스템·로그아웃 흐름, `--admin` 인자
- 콘솔을 별도 브라우저 문맥으로 (로컬 쿠키 공유 회피)
- 감시 규칙: `/auth/me` · `/console/me` 의 401·403 만 정상, 그 외 401·403 · 5xx · 페이지 예외는 문제
- 결과 문서 `docs/vaildates/ui-check-20261007-console.md`, 목록·콘솔 가이드 갱신

## 3. 상세 내용

### 3.1 배경 / 목적
이번 작업(영상 webm 재생, 콘솔 관리자 로그인·회원 관리·시스템)을 단위 테스트뿐 아니라 실제 브라우저에서 눌러 확인.

### 3.2 변경 범위
- 추가: `docs/vaildates/ui-check-20261007-console.md`
- 수정: `scripts/experiments/ui_check.py`, `docs/vaildates/README.md`, `docs/guidance/console-admin.md`

### 3.3 기술 포인트
- 백엔드를 `CONSOLE_REQUIRE_LOGIN=true CONSOLE_ADMINS=uiadmin` 으로 띄워 서버 PC 에서도 로그인 화면이 나오는 배포 조건으로 확인
- 일반 회원 거절은 **맞는 비밀번호**로 확인 (틀린 비밀번호로 거절되는 것과 구별)
- "지금 정리" 는 누르지 않음 — 이 PC 의 개발용 업로드가 실제로 지워짐. 삭제는 단위 테스트로 확인
- 첫 실행에서 `/console/me` 401·403 이 문제로 3건 잡혀 감시 규칙을 고친 뒤 다시 실행

### 3.4 의도적으로 하지 않은 것
- CI 에 Playwright 추가 (dev 서버 3개·모델이 필요해 로컬 점검용 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 실브라우저(Chromium) 17개 흐름 통과, 문제 0건, 종료 코드 0
- [x] 실행 후 테스트 회원(콘솔에서 삭제)·관리자 계정 정리, `uploads/batches` · `uploads/videos` 비어 있음

### 4.2 부작용 / 리스크
- 로컬에서는 사용자 앱·콘솔이 세션 쿠키를 공유 — 운영 가이드에 기록

### 4.3 후속 작업
- 총 병합

### 4.4 관련 문서
- `docs/vaildates/ui-check-20261007-console.md`, `docs/guidance/console-admin.md`
