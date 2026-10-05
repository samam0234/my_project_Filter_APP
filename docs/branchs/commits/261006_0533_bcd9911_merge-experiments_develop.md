# feature/experiments → develop 병합 (no-ff) / `bcd9911ef3dd7bcbf033e24a0a850afae53c01af`

> 브랜치: `develop`
> 작성일: `2026-10-06 05:33`
> 작성자: `agent`
> 파일명: `261006_0533_bcd9911_merge-experiments_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/experiments into develop (no-ff)` |
| **커밋 번호 (SHA)** | `bcd9911ef3dd7bcbf033e24a0a850afae53c01af` |
| **짧은 SHA** | `bcd9911` |
| **브랜치** | `develop` |
| **부모 커밋** | `2399d8b` (develop), `12cf0d4` (feature/experiments 끝) |

## 2. 주 커밋 내용

실험 기반 인스턴스 선택·GrabCut 개선 · 실험 스크립트

병합된 커밋:
- `12cf0d4` docs(branchs): 커밋 기록 58209e0 추가
- `58209e0` perf(vision): 실험 기반 인스턴스 선택·GrabCut 개선과 실험 스크립트

## 3. 상세 내용

### 3.1 배경 / 목적
사용자가 준 파트 작업을 각 브랜치에 모두 커밋한 뒤 **한 번에 총 병합** (2026-10-06).
이전에는 파트마다 병합했으나 규칙 위반이어서, 병합 없이 브랜치별 커밋 상태로 되돌린 뒤 이번에 한 번에 병합했다.

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음
- 병합 순서: agent-rules → langgraph → rag → db-split → feedback-review → prompt-learning → experiments → ops-hardening (쌓인 순서)

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 pytest 전체 통과, 이전 develop 대비 코드 차이는 규칙 파일 20개뿐

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 다음부터는 전체 파트가 끝난 뒤 한 번에 병합

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
