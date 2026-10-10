# 브라우저 확인에서 찾은 검수 중복·되살아남·표기 문제 수정 / `623c4f2467bd687e874b81780f5315ac74280fcb`

> 브랜치: `feature/ui-check`  
> 작성일: `2026-10-06 17:58`  
> 작성자: `agent`  
> 파일명: `261006_1758_623c4f2_ui-check-review-fixes_feature-ui-check.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(console): 브라우저 확인에서 찾은 검수 중복·되살아남·표기 문제 수정` |
| **커밋 번호 (SHA)** | `623c4f2467bd687e874b81780f5315ac74280fcb` |
| **짧은 SHA** | `623c4f2` |
| **브랜치** | `feature/ui-check` |
| **부모 커밋** | `a7cfb31` (develop) |

## 2. 주 커밋 내용

- 브라우저 직접 확인 스크립트 `scripts/experiments/ui_check.py` (Playwright, 9개 흐름, 테스트 계정 자동 정리)
- 확인 중 찾은 문제 4건 수정 (검수 중복 · 삭제 후 되살아남 · 의사 라벨에 묻힘 · 작업 상세 오표기)

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 "다음 할 일" 2번 — 콘솔·화면을 실제 브라우저에서 눌러 확인.
지금까지는 빌드·컴포넌트 테스트만 했다.

### 3.2 변경 범위

- 추가: `scripts/experiments/ui_check.py`, `docs/vaildates/ui-check-20261006.md`
- 수정: `backend/app/services/{learning_catalog,learning_review}.py`, `console/src/pages/LearningPage{,.test}.tsx`,
  `frontend/src/pages/JobDetailPage.tsx`, `tests/unit/test_learning_review.py`,
  `docs/{vaildates/README.md, guidance/console-admin.md}`, `scripts/README.md`

### 3.3 기술 포인트

- 좋아요·교정 → 같은 job 의 요청 후보에 합침 (`_merge_into_request`): 출처 승격, origin_id 를 피드백으로 옮겨 삭제 시 사이드카 정리
- 요청 후보 재생성 검사를 "같은 작업 또는 같은 문장, 출처 무관" 으로 — 합쳐진 뒤 삭제된 표식도 인식
- 콘솔 기본 필터 `source=user` (API 가 `user` 별칭과 쉼표 목록 지원)
- 5173 포트를 다른 프로젝트 dev 서버가 쓰고 있어 첫 실행이 엉뚱한 앱을 봄 → 스크립트에 `--app`·`--console` 인자

### 3.4 의도적으로 하지 않은 것

- 브라우저 E2E 를 CI 에 넣기 (백엔드 모델·Ollama 필요 — 로컬 확인용)
- 비로그인 `/auth/me` 401 을 200 으로 바꾸기 (동작 정상, 브라우저 콘솔 소음만)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 브라우저 9/9 통과, 브라우저 오류(콘솔 error · 페이지 예외 · 5xx · 예상 밖 401) 0건
- [x] 검수 목록: 요청 + 좋아요 → 1건(출처 좋아요)
- [x] pytest 전체 통과 (신규 3건, 삭제 테스트 갱신), console vitest 4 · frontend vitest 16, 두 앱 빌드 성공
- [x] 실행 중 만든 테스트 계정 4개·작업·피드백·샘플 모두 정리

### 4.2 부작용 / 리스크

- 같은 작업의 피드백이 요청 후보를 덮으므로, 운영자가 고쳐 승인한 정답 위에 사용자 교정이 오면 사용자 값으로 바뀌고 다시 검수 대기

### 4.3 후속 작업

- 4번 학습 루프, 5번 세그 개선

### 4.4 관련 문서

- `docs/vaildates/ui-check-20261006.md`
