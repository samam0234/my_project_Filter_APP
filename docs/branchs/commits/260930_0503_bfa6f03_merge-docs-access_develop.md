# feature/docs-access → develop 병합 (no-ff) / `bfa6f0322c83c853d3f52ea8e35b7852ddef0d1a`

> 브랜치: `develop`
> 작성일: `2026-09-30 05:03`
> 작성자: `agent`
> 파일명: `260930_0503_bfa6f03_merge-docs-access_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/docs-access into develop (no-ff)` |
| **커밋 번호 (SHA)** | `bfa6f0322c83c853d3f52ea8e35b7852ddef0d1a` |
| **짧은 SHA** | `bfa6f03` |
| **브랜치** | `develop` |
| **부모 커밋** | `c78b81e` (develop), `b651e1c` (feature tip) |

## 2. 주 커밋 내용

- 접근 정책 반영 문서 전면 갱신 (`d383ccd`, 24개 파일)

## 3. 상세 내용

### 3.1 배경 / 목적

계정 기능(로그인 · 회원가입 · 아이디/비밀번호 찾기)과 접근 정책(비로그인 다운로드만 · 회원 전용 기록/피드백/배치 ·
콘솔 loopback), 이를 반영한 문서를 통합 라인 develop 에 넣는다. 순서: feature/auth → feature/docs-access.

### 3.2 변경 범위

- `docs/` (API · guidance · Architecture · plan · vaildates · web_management · find_debug), 폴더 README, RUN, AGENTS, `.env.example`
- 기록: `260930_0503_d383ccd…`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 충돌 없음 (feature/docs-access 는 feature/auth 끝에서 분기)

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 두 병합 후 develop 에서 pytest 164개 통과, `npm run build` 통과

### 4.2 부작용 / 리스크

- 백엔드 재시작 시 기존 DB 에 `users`·`auth_sessions`·`auth_codes` 생성, `jobs.user_id`·`batch_jobs.user_id` 추가 (자동)
- 소유자 없는 기존 작업(18건)은 사용자 앱에서 보이지 않고 콘솔에서만 조회
- 콘솔은 백엔드와 같은 PC 에서만 전체 조회 가능

### 4.3 후속 작업

- (선택) `git push origin develop` 및 feature 브랜치
- 배포 전: `SECRET_KEY` · `SMTP_*` · `SESSION_COOKIE_SECURE=true` (`docs/web_management/pre-deploy.md`)

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`, `docs/guidance/auth.md`
