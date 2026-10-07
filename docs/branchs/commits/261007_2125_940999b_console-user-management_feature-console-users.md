# 회원 관리 화면 — 검색·잠금 해제·세션 끊기·계정 삭제 / `940999bd579c160b6c9e705a8dc7040466195b1e`

> 브랜치: `feature/console-users`  
> 작성일: `2026-10-07 21:25`  
> 작성자: `agent`  
> 파일명: `261007_2125_940999b_console-user-management_feature-console-users.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(console): 회원 관리 화면 — 검색·잠금 해제·세션 끊기·계정 삭제` |
| **커밋 번호 (SHA)** | `940999bd579c160b6c9e705a8dc7040466195b1e` |
| **짧은 SHA** | `940999b` |
| **브랜치** | `feature/console-users` |
| **부모 커밋** | `54e0559` |

## 2. 주 커밋 내용

- 서비스 `backend/app/services/user_admin.py`: 목록(GROUP BY 집계) · 잠금 해제 · 세션 끊기 · 계정 삭제
- API `GET /console/users` · `POST /users/{id}/unlock` · `POST /users/{id}/sessions/revoke` · `DELETE /users/{id}`
- 콘솔 "회원 관리" 메뉴(`UsersPage`): 검색, 상태 표시, 동작 버튼, 아이디 재입력 삭제 확인, 페이지 이동
- 배치·작업 화면의 "서버 PC 에서만" 안내를 관리자 로그인 기준으로 수정

## 3. 상세 내용

### 3.1 배경 / 목적
회원 잠김·유출 의심·탈퇴 요청을 처리하려면 DB 를 직접 고쳐야 했다. 관리자 로그인(`afa4033`)이 생겨 원격에서 회원 데이터를 다룰 수 있는 기반이 마련됐다.

### 3.2 변경 범위
- 추가: `backend/app/services/user_admin.py`, `tests/unit/test_console_users.py`, `console/src/pages/UsersPage.tsx`, `UsersPage.test.tsx`
- 수정: `backend/app/routers/console.py`, `console/src/{api/client.ts, types/index.ts, components/Sidebar.tsx, App.tsx, pages/BatchesPage.tsx, pages/JobsPage.tsx}`,
  `docs/guidance/console-admin.md`, `docs/API_DOCUMENTATION.md`

### 3.3 기술 포인트
- 삭제 범위: 계정·세션·재설정 코드·작업(행+`uploads/{id}`)·배치(행+`uploads/batches/{id}`)·영상(`owner.json` 으로 찾은 `uploads/videos/{id}`)
- 학습 DB 샘플은 `user_id` 만 NULL — 검수된 문장은 RAG·LoRA 데이터라 운영자가 "학습 데이터" 화면에서 따로 판단
- SQLite 는 FK CASCADE 가 꺼져 있을 수 있어 세션·코드를 직접 삭제
- 경로는 업로드 루트 안인지 확인 후에만 rmtree
- 보호: 관리자(`CONSOLE_ADMINS`)·현재 로그인한 본인 삭제 불가, 확인 아이디 불일치 400
- 비밀번호 해시는 응답에 넣지 않음

### 3.4 의도적으로 하지 않은 것
- 관리자 지정·해제 UI (설정 파일로만 — 권한 상승 경로를 화면에 두지 않음), 회원 정보 수정, 감사 로그 테이블

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과 (신규 6건: 목록·검색, 잠금 해제, 세션 끊기, 파일 포함 삭제, 관리자·본인 보호, 권한)
- [x] 콘솔 vitest 18 · build 통과

### 4.2 부작용 / 리스크
- 삭제는 되돌릴 수 없음 — 서버 로그(`회원 삭제 ... by=`)로만 추적

### 4.3 후속 작업
- `feature/console-system` (시스템 상태·저장 공간·정리)

### 4.4 관련 문서
- `docs/guidance/console-admin.md` (회원 관리 절), `docs/API_DOCUMENTATION.md`
