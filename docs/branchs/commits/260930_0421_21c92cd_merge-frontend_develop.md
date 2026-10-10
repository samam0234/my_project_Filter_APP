# feature/frontend → develop 병합 (no-ff) / `21c92cdf30c52317a61847378f96c377220cb182`

> 브랜치: `develop`
> 작성일: `2026-09-30 04:21`
> 작성자: `agent`
> 파일명: `260930_0421_21c92cd_merge-frontend_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/frontend into develop (no-ff)` |
| **커밋 번호 (SHA)** | `21c92cdf30c52317a61847378f96c377220cb182` |
| **짧은 SHA** | `21c92cd` |
| **브랜치** | `develop` |
| **부모 커밋** | `a471058` (develop), `eee21cb` (feature tip) |

## 2. 주 커밋 내용

- package-lock libc 필드 정리 (`bdb4498`)
- 사용자 앱 6개 페이지와 정답 알려주기 (`3ad0396`)
- 프론트 문서 (`5bf188f`), MVP 체크리스트 사용자 앱 항목 (`791d0b3`)

## 3. 상세 내용

### 3.1 배경 / 목적

인스턴스 선택·LoRA(A~E), 문서 전면 갱신, 사용자 앱 페이지 개편을 통합 라인 develop 에 반영한다.
병합 순서는 instance → docs → frontend (docs·frontend 는 instance 끝에서 분기).

### 3.2 변경 범위

- `frontend/src/` (router · pages 7개 · components · hooks · data)
- `frontend/README.md`, `docs/guidance/user-frontend.md`, `docs/Architecture/apps.md`, `docs/vaildates/mvp-checklist.md`
- 기록: `260930_0404_bdb4498…`, `260930_0420_3ad0396…`, `260930_0420_5bf188f…`, `260930_0421_791d0b3…`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 충돌: `docs/vaildates/mvp-checklist.md` — docs 가 2~4번, frontend 가 5번을 고쳐 인접 줄 충돌 → 2~4번은 docs, 5번은 frontend 값으로 양쪽 유지

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 3건 병합 후 develop 에서 pytest 132개 통과, `npm run build` 통과, 백엔드 `/health` 200

### 4.2 부작용 / 리스크

- 사용자 로컬 Vite(:5173)·백엔드(`--reload`)는 develop 코드로 자동 반영됨

### 4.3 후속 작업

- (선택) `git push origin develop` 및 각 feature 브랜치
- main 은 release 경유 후 `--no-ff`

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
