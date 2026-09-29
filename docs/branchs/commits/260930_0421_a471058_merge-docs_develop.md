# feature/docs → develop 병합 (no-ff) / `a471058621a0f84a671eda28ee633127f9e58da4`

> 브랜치: `develop`
> 작성일: `2026-09-30 04:21`
> 작성자: `agent`
> 파일명: `260930_0421_a471058_merge-docs_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/docs into develop (no-ff)` |
| **커밋 번호 (SHA)** | `a471058621a0f84a671eda28ee633127f9e58da4` |
| **짧은 SHA** | `a471058` |
| **브랜치** | `develop` |
| **부모 커밋** | `fe74513` (develop), `b4428a0` (feature tip) |

## 2. 주 커밋 내용

- 인스턴스 선택·LoRA·폴더 분리 반영 문서 전면 갱신 (`e688159`, 27개 파일)

## 3. 상세 내용

### 3.1 배경 / 목적

인스턴스 선택·LoRA(A~E), 문서 전면 갱신, 사용자 앱 페이지 개편을 통합 라인 develop 에 반영한다.
병합 순서는 instance → docs → frontend (docs·frontend 는 instance 끝에서 분기).

### 3.2 변경 범위

- `docs/` (API · WORKFLOW · llm-and-vision · plan/* · find_debug/2026-09-29.md 등), 루트·폴더 README, AGENTS·SKILL
- 기록: `260930_0409_e688159…`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 충돌 없음 (instance 끝에서 분기)

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 3건 병합 후 develop 에서 pytest 132개 통과, `npm run build` 통과, 백엔드 `/health` 200

### 4.2 부작용 / 리스크

- 없음 (문서만)

### 4.3 후속 작업

- (선택) `git push origin develop` 및 각 feature 브랜치
- main 은 release 경유 후 `--no-ff`

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
