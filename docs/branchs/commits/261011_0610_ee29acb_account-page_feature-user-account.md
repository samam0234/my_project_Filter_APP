# 내 계정 페이지와 헤더 프로필 메뉴 추가 / `ee29acb41eb58fae5b100717c2291164d2e6e785`

> 브랜치: `feature/user-account`  
> 작성일: `2026-10-11 06:10`  
> 작성자: `agent`  
> 파일명: `261011_0610_ee29acb_account-page_feature-user-account.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(account): 내 계정 페이지와 헤더 프로필 메뉴 추가` |
| **커밋 번호 (SHA)** | `ee29acb41eb58fae5b100717c2291164d2e6e785` |
| **짧은 SHA** | `ee29acb` |
| **브랜치** | `feature/user-account` |
| **부모 커밋** | `3750558` |

## 2. 주 커밋 내용

- 헤더 프로필 클릭 → 메뉴(이름 · 이메일 · 내 계정 · 작업 기록 · 배치 · 로그아웃), Esc · 바깥 클릭 · 화면 이동으로 닫힘
- `/account` 내 계정 페이지 (`?tab=` 구역): 내 정보 · 작업 기록 · 보안 · 보관/탈퇴
- 작업 기록은 헤더 메뉴에서 제거, `HistoryPanel` 로 내 계정 안에 이동 (`/history` 는 리다이렉트)
- 백엔드 계정 API 4종: `PATCH /auth/me` · `POST /auth/password/change` · `POST /auth/logout-all` · `DELETE /auth/me`

## 3. 상세 내용

### 3.1 배경 / 목적
프로필을 눌러도 작업 기록으로만 가고 사용자 정보·보안 설정·탈퇴 화면이 없었다. 법적 문서에도 "스스로 탈퇴 화면 없음"이 남아 있었다.

### 3.2 변경 범위
- 백엔드: `routers/auth.py`, `schemas/auth.py`, `services/auth_service.py`
- 프런트: `pages/AccountPage.tsx`, `components/account/HistoryPanel.tsx`(HistoryPage 이동), `components/layout/AppLayout.tsx`, `App.tsx`, `api/client.ts`, `store/useAuthStore.ts`, 링크(HomePage · JobDetailPage)
- 문서: API_DOCUMENTATION · FEATURES · user-frontend · auth · legal · frontend/README

### 3.3 기술 포인트
- 비밀번호 변경: 현재 비밀번호 확인 → 모든 세션 폐기 후 지금 기기 세션만 다시 등록
- 탈퇴: 콘솔과 같은 `user_admin.delete_user` 재사용 (작업 · 배치 · 영상 삭제, 학습 DB 는 연결만 해제)
- 운영자(`CONSOLE_ADMINS`) 계정은 스스로 탈퇴 불가 (콘솔 접근 상실 방지)

### 3.4 의도적으로 하지 않은 것
- 이메일 변경 (소유 확인 메일이 필요해 후속)
- 로그인 기기 목록 보기

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과 (계정 테스트 +6, 문서 커버리지 포함)
- [x] 프런트 vitest 75건 통과, tsc · 빌드 통과

### 4.2 부작용 / 리스크
- 예전 `/history` 북마크는 리다이렉트로 유지
- 아직 병합 · 푸시 · 서버 배포 전

### 4.3 후속 작업
- 사용자 지시 후 총 병합 → 서버 배포
