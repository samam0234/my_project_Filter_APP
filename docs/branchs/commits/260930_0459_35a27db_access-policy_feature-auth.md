# 비로그인 저장 제한과 회원 전용 접근 정책 적용 / `35a27db040c91451373f3ce5dfcc5ab80327deea`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 04:59`
> 작성자: `agent`
> 파일명: `260930_0459_35a27db_access-policy_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(auth): 비로그인 저장 제한과 회원 전용 접근 정책 적용` |
| **커밋 번호 (SHA)** | `35a27db040c91451373f3ce5dfcc5ab80327deea` |
| **짧은 SHA** | `35a27db` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `ef42901` |

## 2. 주 커밋 내용

- 비로그인 업로드: 저장 없음(DB·파일·실패 케이스), 결과는 data URL 로만 (`saved=false`)
- 로그인: 작업 기록·상세·파일·피드백·배치 모두 본인 것만, 남의 것은 404
- 콘솔 전용 API `/api/v1/console/*` (loopback 한정, `CONSOLE_ALLOW_REMOTE`)
- `batch_jobs.user_id`, 공용 테스트 fixture, 접근 정책 테스트

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 요청:
- 작업 기록 화면이 "Request failed with status code 500" — 로그인 시에만 보이게
- 비로그인: 배경 제거는 가능하되 저장 없이 다운로드만
- 배치: 로그인 회원 전용
- 로그인 회원은 비로그인 기능 + 저장·기록·배치

500 의 직접 원인은 백엔드(:8000)가 꺼져 있어 Vite 프록시가 본문 없는 500 을 돌려준 것.
화면 문구도 알아볼 수 있게 바꿨다.

### 3.2 변경 범위

- 추가: `backend/app/core/access.py`, `backend/app/routers/console.py`, `tests/unit/conftest.py`, `tests/unit/test_access.py`
- 수정: `core/config.py`, `db/session.py`, `models/batch_job.py`, `repositories/batch_repository.py`,
  `routers/{batch,feedback,jobs,router,upload}.py`, `schemas/response.py`, `workflows/{graph,nodes,state}.py`, `tests/unit/test_auth.py`

### 3.3 기술 포인트

- `run_pipeline(persist=False)` → `feedback_collector` 는 이미지·DB 를 남기지 않고 통과
- 비로그인 응답은 after 파일을 base64 로 담은 뒤 `upload_path/{job_id}` 를 즉시 삭제 (`finally`)
- `owned_job`: 없음·비로그인·타인 소유를 모두 같은 404 로 — 작업 ID 존재 여부 노출 없음
- 콘솔 파일 경로는 `before/after` 만 허용하고 `..`·경로 구분자 거부
- `TestClient` 의 클라이언트 주소는 `testclient` 라 loopback 이 아님 → 콘솔 403 검증 가능

### 3.4 의도적으로 하지 않은 것

- 소유자 없는(user_id NULL) 기존 작업 18건을 특정 계정에 귀속 — 사용자 앱에서는 보이지 않고 콘솔에서만 조회
- 콘솔 로그인/관리자 권한 (loopback 제한으로 대체)
- 결과 파일 서명 URL (쿠키 + 소유자 확인으로 충분)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 전체 164개 통과 (접근 정책 10개 신규)
- [x] 프론트 `tsc -b` 통과
- [x] 실서버: 비로그인 `/jobs`·`/batch` 401, 콘솔 API(로컬) 200,
      비로그인 업로드 `saved=false` · data URL(431 KB) · 업로드 폴더 생성 없음
- [x] 기존 SQLite 에 `batch_jobs.user_id` 자동 추가
- [x] headless Chrome: 비로그인 작업 기록·배치 잠금 안내 + 메뉴 자물쇠, 회원 배치 화면·헤더
- 검증용 계정은 확인 후 삭제
- [ ] 콘솔 타입 검사 — `console/node_modules` 미설치 (변경은 API 경로 문자열 2곳)

### 4.2 부작용 / 리스크

- 사용자 앱에서 기존 작업 18건(로그인 기능 이전)이 보이지 않음 — 콘솔에서만
- 비로그인 결과는 새로고침하면 사라짐 (의도) — 화면에 안내
- 콘솔을 백엔드와 다른 PC 에서 쓰면 403 — `CONSOLE_ALLOW_REMOTE=true` 는 앞단 접근 제어가 있을 때만

### 4.3 후속 작업

- develop 병합
- (선택) 기존 무소유 작업을 관리자 계정에 귀속하는 스크립트

### 4.4 관련 문서

- `docs/guidance/auth.md` (접근 정책 절)
- `docs/API_DOCUMENTATION.md`
