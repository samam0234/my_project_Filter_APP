# feature/vite-upgrade → develop 병합 (no-ff) / `9b216477f849e51cdc2b2a16420b89ebfb96cc0e`

> 브랜치: `develop`
> 작성일: `2026-10-06 20:05`
> 작성자: `agent`
> 파일명: `261006_2005_9b21647_merge-vite-upgrade_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/vite-upgrade into develop (no-ff)` |
| **커밋 번호 (SHA)** | `9b216477f849e51cdc2b2a16420b89ebfb96cc0e` |
| **짧은 SHA** | `9b21647` |
| **브랜치** | `develop` |
| **부모 커밋** | `17f9f07` (develop), `a2b5dd4` (feature/vite-upgrade 끝) |

## 2. 주 커밋 내용

vite 7 · vitest 5 개발 도구 업그레이드 (npm audit 치명 0, Node 22.12 요구)

병합된 커밋:
- `a2b5dd4` docs(branchs): 커밋 기록 86df870 추가
- `86df870` chore(deps): vite 7 · vitest 5 로 개발 도구 업그레이드

## 3. 상세 내용

### 3.1 배경 / 목적
남은 항목(배포 제외)의 ONNX 추론 · vite 업그레이드를 각 브랜치에 모두 커밋한 뒤 **한 번에 총 병합** (2026-10-06, 병합 시점 규칙).

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음
- 병합 순서: onnx-infer → vite-upgrade (서로 독립, 둘 다 develop 에서 분기)

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 pytest 전체 · frontend 16 · console 4 테스트 통과, 두 앱 빌드 성공

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 다음부터는 전체 파트가 끝난 뒤 한 번에 병합

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
