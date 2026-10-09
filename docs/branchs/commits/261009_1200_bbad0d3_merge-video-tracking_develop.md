# feature/video-tracking → develop 병합 (no-ff) / `bbad0d39442c9520ede0f6df900160db91c5ebc0`

> 브랜치: `develop`
> 작성일: `2026-10-09 12:00`
> 작성자: `agent`
> 파일명: `261009_1200_bbad0d3_merge-video-tracking_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/video-tracking into develop (no-ff)` |
| **커밋 번호 (SHA)** | `bbad0d39442c9520ede0f6df900160db91c5ebc0` |
| **짧은 SHA** | `bbad0d3` |
| **브랜치** | `develop` |
| **부모 커밋** | `ac6d81c` (develop), `2eb74b5` (feature/video-tracking 끝) |

## 2. 주 커밋 내용

영상 · GIF 에서 고른 대상을 프레임 사이로 따라가기 (서로 지나가도 유지)

병합된 커밋:
- `2eb74b5` docs(branchs): 커밋 기록 a755909 추가
- `a755909` feat(video): 영상 · GIF 에서 "왼쪽 사람"처럼 고른 대상을 프레임 사이로 따라가기

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
