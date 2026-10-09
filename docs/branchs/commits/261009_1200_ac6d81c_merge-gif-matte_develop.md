# feature/gif-matte → develop 병합 (no-ff) / `ac6d81cbb0e0392519207cc64cfc9d492649cc84`

> 브랜치: `develop`
> 작성일: `2026-10-09 12:00`
> 작성자: `agent`
> 파일명: `261009_1200_ac6d81c_merge-gif-matte_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/gif-matte into develop (no-ff)` |
| **커밋 번호 (SHA)** | `ac6d81cbb0e0392519207cc64cfc9d492649cc84` |
| **짧은 SHA** | `ac6d81c` |
| **브랜치** | `develop` |
| **부모 커밋** | `05a66ac` (develop), `7acf8b6` (feature/gif-matte 끝) |

## 2. 주 커밋 내용

GIF 경계를 올릴 배경색(밝은 · 어두운)에 맞춰 부드럽게 — 매트 옵션

병합된 커밋:
- `7acf8b6` docs(branchs): 커밋 기록 a8cb4b3 추가
- `a8cb4b3` feat(gif): 배경 제거 GIF 경계를 올릴 배경색(밝은 · 어두운)에 맞춰 부드럽게 — 매트

## 3. 상세 내용

### 3.1 배경 / 목적
사용자가 준 전체 파트를 각 브랜치에 모두 커밋한 뒤 사용자 지시("병합 ㄱ")로 **한 번에 총 병합** (2026-10-09, 병합 시점 규칙).

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음
- 브랜치가 앞 브랜치 위에 쌓여 있어 쌓인 순서대로 병합: docs-refresh → deploy-https-mail-policy → service-db-mariadb → model-fetch → video-removal-propagate → gif-matte → video-tracking → lora-compositional → yolo-retrain

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 백엔드 pytest 432 · 프론트 vitest 54 통과 (병합 결과 트리는 feature/yolo-retrain 과 동일)

### 4.2 부작용 / 리스크
- 없음. 모델 파일(LoRA 배포본 교체)은 git 밖이라 서버에는 따로 반영 필요

### 4.3 후속 작업
- COCO 밖 실패 사진 수집 · 라벨링 후 YOLO 재학습, 체인 + LoRA 비교

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
