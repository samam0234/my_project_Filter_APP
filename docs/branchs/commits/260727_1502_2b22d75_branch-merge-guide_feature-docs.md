# Branch merge guide (feature work / develop-main integrate) / `2b22d75`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-27`  
> 파일명: `260727_1502_2b22d75_branch-merge-guide_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(guidance): require feature work and develop/main-only linear merges` |
| **짧은 SHA** | `2b22d75` |
| **브랜치** | `feature/docs` |
| **부모 커밋** | `557642d` 계열 (직전 feature/docs HEAD) |

## 2. 주 커밋 내용

- `docs/guidance/branch-merge.md` 신설
- 작업은 feature, 일자 병합은 develop/main 만 규칙 문서화
- BRANCH_MAP, plan Git 전략, agents, cursor, grok 스킬 동기화

## 3. 상세 내용

### 3.1 배경 / 목적
Git Graph가 일자인 이유를 정책으로 명확히 하고, 통합 창구를 develop/main 으로 고정한다.

### 3.2 변경 범위
- 추가: `docs/guidance/branch-merge.md`
- 수정: branchs, plan, guidance README, agents, cursor, grok, 루트 README

### 3.3 기술 포인트
- FF 일자 통합 허용
- feature→feature 장기 통합 금지

### 3.4 의도적으로 하지 않은 것
- git hook 강제
- 기존 브랜치 재배치

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 가이드 커밋 완료 (`feature/docs`)

### 4.2 부작용 / 리스크
없음

### 4.3 후속 작업
- develop 병합 시 본 규칙 준수

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
