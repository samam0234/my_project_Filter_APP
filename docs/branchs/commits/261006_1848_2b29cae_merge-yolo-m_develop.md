# feature/yolo-m → develop 병합 (no-ff) / `2b29cae7f3989101bf6cb7123448b49ff08ef6f8`

> 브랜치: `develop`
> 작성일: `2026-10-06 18:48`
> 작성자: `agent`
> 파일명: `261006_1848_2b29cae_merge-yolo-m_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/yolo-m into develop (no-ff)` |
| **커밋 번호 (SHA)** | `2b29cae7f3989101bf6cb7123448b49ff08ef6f8` |
| **짧은 SHA** | `2b29cae` |
| **브랜치** | `develop` |
| **부모 커밋** | `ba1ccd3` (develop), `0cf6e46` (feature/yolo-m 끝) |

## 2. 주 커밋 내용

서빙 세그 모델 YOLO26m-seg 교체(공정 비교 검출률 81.1→88.0%), 재시도 신뢰도 버그 수정

병합된 커밋:
- `0cf6e46` docs(branchs): 커밋 기록 2be3b35 추가
- `2be3b35` feat(vision): 서빙 세그 모델을 YOLO26m-seg 로 교체하고 재시도 신뢰도 버그 수정

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 "다음 할 일" 1·2·4·5번(3번 배포 제외)을 각 브랜치에 모두 커밋한 뒤 **한 번에 총 병합** (2026-10-06, 병합 시점 규칙).

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음
- 병합 순서: docker-verify (독립) → ui-check → retrain-loop → yolo-m (쌓인 순서)

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
