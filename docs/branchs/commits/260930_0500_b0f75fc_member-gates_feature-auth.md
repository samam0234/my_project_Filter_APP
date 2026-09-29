# 회원 전용 화면 게이트와 비로그인 다운로드 전용 작업실 / `b0f75fc84db683ed932eb7097a2ca40c19a9afb7`

> 브랜치: `feature/auth`
> 작성일: `2026-09-30 05:00`
> 작성자: `agent`
> 파일명: `260930_0500_b0f75fc_member-gates_feature-auth.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(frontend): 회원 전용 화면 게이트와 비로그인 다운로드 전용 작업실` |
| **커밋 번호 (SHA)** | `b0f75fc84db683ed932eb7097a2ca40c19a9afb7` |
| **짧은 SHA** | `b0f75fc` |
| **브랜치** | `feature/auth` |
| **부모 커밋** | `38a1a3b` |

## 2. 주 커밋 내용

- `RequireLogin` 게이트 (작업 기록 · 작업 상세 · 배치)
- 작업실 비로그인: 저장 안 됨 안내 · 피드백/상세 숨김 · 원본은 로컬 미리보기
- 메뉴 자물쇠, 홈 "내 최근 작업" 로그인 시에만, 작업 기록 항상 본인 작업
- 5xx(백엔드 꺼짐) 오류 문구 개선

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

- 추가: `frontend/src/components/auth/RequireLogin.tsx`
- 수정: `api/client.ts`, `types/index.ts`, `hooks/{useApi,useImageProcessing}.ts`, `components/layout/AppLayout.tsx`,
  `pages/{Batch,Guide,History,Home,JobDetail,Studio}Page.tsx`

### 3.3 기술 포인트

- `useJobs(limit, enabled)` — 비로그인이면 요청 자체를 보내지 않음 (401 노이즈 방지)
- 비로그인 결과 `after_url` 은 data URL — `<img>`·다운로드 링크에 그대로 사용
- 로그아웃 시 작업실 결과를 비워, 로그인 때 만든 결과의 피드백 버튼이 비로그인에서 401 나지 않게 함

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
