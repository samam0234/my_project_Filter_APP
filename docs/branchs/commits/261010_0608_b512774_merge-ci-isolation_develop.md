# feature/ci-isolation → develop 병합 (no-ff) / `b512774cf167ebd11fd95f4b2ae91924c16aa829`

> 브랜치: `develop`
> 작성일: `2026-10-10 06:08`
> 작성자: `agent`
> 파일명: `261010_0608_b512774_merge-ci-isolation_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/ci-isolation into develop (no-ff)` |
| **커밋 번호 (SHA)** | `b512774cf167ebd11fd95f4b2ae91924c16aa829` |
| **짧은 SHA** | `b512774` |
| **브랜치** | `develop` |
| **부모 커밋** | `4d40ad2` (develop), `a1b150c` (feature/ci-isolation 끝) |

## 2. 주 커밋 내용

라우터 밖 DB 세션도 테스트 DB 로 묶기, CI 설치 충돌 수정 · pip-audit · 주간 실행

병합된 커밋:
- `a1b150c` docs(branchs): 커밋 기록 d6236a3 추가
- `d6236a3` fix(test): 라우터 밖 DB 세션도 테스트 DB 로 묶기, CI 설치 충돌 · 의존성 점검 추가

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시("마무리로 전체 문서 업데이트 … 커밋 작업 후 최종적으로 병합하고 푸시까지", 2026-10-10)에 따라, 문서 정리 중 발견한 의존성 보안 · 테스트 격리 수정과 문서 정리를 각 브랜치에 모두 커밋한 뒤 **한 번에 총 병합**하고 origin 에 push.

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음 (병합 결과 트리 = feature/docs-final)
- 쌓인 순서대로: deps-security → ci-isolation → docs-final

### 3.4 의도적으로 하지 않은 것
- main 병합 (develop 만 push)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 백엔드 pytest 451 · 프론트 vitest 54 · 콘솔 21 통과

### 4.2 부작용 / 리스크
- 의존성 판이 크게 올랐다(FastAPI 0.143 · starlette 1.7 · LangGraph 1.2) — 서버에서 다시 빌드할 때 반영
- push 후 GitHub Actions 결과 확인 필요

### 4.3 후속 작업
- 실서버 배포 (docs/DEPLOYMENT.md), main 병합은 배포 검증 뒤

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
