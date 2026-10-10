# 콘솔 작업 조회를 콘솔 전용 API 로 전환 / `38a1a3be0add3cda6b4418057ae4dd0a1c4d3650`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 04:59`
> 작성자: `agent`
> 파일명: `260930_0459_38a1a3b_console-api_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(console): 콘솔 작업 조회를 콘솔 전용 API 로 전환` |
| **커밋 번호 (SHA)** | `38a1a3be0add3cda6b4418057ae4dd0a1c4d3650` |
| **짧은 SHA** | `38a1a3b` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `35a27db` |

## 2. 주 커밋 내용

- `console/src/api/client.ts`: `/api/v1/jobs` → `/api/v1/console/jobs`, 단건도 동일
- `JobsPage` 설명 문구 갱신

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

- 수정: `console/src/api/client.ts`, `console/src/pages/JobsPage.tsx`

### 3.3 기술 포인트

- 사용자 앱 `/jobs` 가 본인 작업만 돌려주면서 콘솔 대시보드가 비는 것을 방지
- 결과 링크는 서버가 콘솔 파일 경로로 바꿔 내려주므로 콘솔 코드 추가 변경 없음

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
