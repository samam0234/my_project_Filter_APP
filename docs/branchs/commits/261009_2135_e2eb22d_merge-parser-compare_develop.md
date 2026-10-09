# feature/parser-compare → develop 병합 (no-ff) / `e2eb22d320fd79160e3babcbd2d4b00a8fac86cc`

> 브랜치: `develop`
> 작성일: `2026-10-09 21:35`
> 작성자: `agent`
> 파일명: `261009_2135_e2eb22d_merge-parser-compare_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/parser-compare into develop (no-ff)` |
| **커밋 번호 (SHA)** | `e2eb22d320fd79160e3babcbd2d4b00a8fac86cc` |
| **짧은 SHA** | `e2eb22d` |
| **브랜치** | `develop` |
| **부모 커밋** | `b69df33` (develop), `40926af` (feature/parser-compare 끝) |

## 2. 주 커밋 내용

해석기 비교(Ollama 체인 · LoRA · 혼합) 와 PROMPT_SECOND_OPINION 설정

병합된 커밋:
- `40926af` docs(branchs): 커밋 기록 bbfc671 추가
- `bbfc671` feat(llm): 해석기 비교 — 혼합(LoRA 먼저 · 갈리면 Ollama)이 지금 체인보다 정확 · 빠름, PROMPT_SECOND_OPINION 로 켤 수 있게

## 3. 상세 내용

### 3.1 배경 / 목적
"아직 부족한 부분" 작업과 이어진 남은 작업을 각 브랜치에 모두 커밋한 뒤, 사용자 지시("커밋 작업 후 최종적으로 병합")로 **한 번에 총 병합** (2026-10-09 밤, 병합 시점 규칙).

### 3.2 변경 범위
- 브랜치 내용은 각 브랜치의 커밋 기록 md 참고 (`docs/branchs/commits/`)

### 3.3 기술 포인트
- `git merge --no-ff`. 충돌은 docker-lora 1건(`docs/vaildates/parser-compare-20261009.md` 의 "다음" 목록 — lora-selector 와 같은 줄을 고침)뿐이고 양쪽 새 내용을 합쳐 풀었다. 그 병합 커밋 메시지에 `# Conflicts` 기록 줄이 남아 있다
- 순서: video-removal-pan → tracking-hard → parser-compare → seg-labeling → deploy-rehearsal (쌓인 순서) → lora-selector · docker-lora · hard-example-consent (deploy-rehearsal 에서 갈라진 세 갈래, 별도 작업 폴더에서 작업)

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 총 병합 후 백엔드 pytest 447 · 프론트 vitest 54 · 타입 검사 통과

### 4.2 부작용 / 리스크
- 모델 파일(LoRA 배포본 교체)은 git 밖이라 서버에는 따로 반영 필요 (scripts/models_bundle.py)
- 백엔드가 새 코드로 뜨면 FEEDBACK_IMAGE_RETENTION_DAYS(30일) 지난 실패 사진이 정리된다 — 지금 있는 4장은 2026-10-08 것이라 11-07 이후

### 4.3 후속 작업
- 실서버 리허설(deploy_check), 실패 사진 수집(HARD_EXAMPLE_CONF) 결정 · 라벨링 후 YOLO 재학습, 승인 문장으로 해석기 재비교 후 GPU 서버 기본값 결정

### 4.4 관련 문서
- `docs/guidance/branch-merge.md`
