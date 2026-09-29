# feature/instance → develop 병합 (no-ff) / `fe74513146ce00f8f190d74c019346b8766f26a1`

> 브랜치: `develop`
> 작성일: `2026-09-30 04:21`
> 작성자: `agent`
> 파일명: `260930_0421_fe74513_merge-instance_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/instance into develop (no-ff)` |
| **커밋 번호 (SHA)** | `fe74513146ce00f8f190d74c019346b8766f26a1` |
| **짧은 SHA** | `fe74513` |
| **브랜치** | `develop` |
| **부모 커밋** | `80fa40b` (develop), `4bb93fc` (feature tip) |

## 2. 주 커밋 내용

- 특정 인스턴스 선택·물체 지우기 (`c65314f`)
- 라벨 별칭·ONNX 세션 가드 (`3970b1b`)
- 인스턴스 선택 프롬프트 LoRA 학습·평가·서빙 (`793113a`)

## 3. 상세 내용

### 3.1 배경 / 목적

인스턴스 선택·LoRA(A~E), 문서 전면 갱신, 사용자 앱 페이지 개편을 통합 라인 develop 에 반영한다.
병합 순서는 instance → docs → frontend (docs·frontend 는 instance 끝에서 분기).

### 3.2 변경 범위

- `backend/app/services/` (instance_selector · prompt_spec · prompt_lora · segmentation · effects …)
- `training/lora/` (시드 · eval_parser · 정책), `tests/unit/` 신규 3개
- 기록: `260930_0258_c65314f…`, `260930_0358_3970b1b…`, `260930_0359_793113a…`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 충돌 없음

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 3건 병합 후 develop 에서 pytest 132개 통과, `npm run build` 통과, 백엔드 `/health` 200

### 4.2 부작용 / 리스크

- LoRA 서빙(`LLM_PROVIDER=lora`)은 선택 사항. 기본은 Ollama 유지

### 4.3 후속 작업

- (선택) `git push origin develop` 및 각 feature 브랜치
- main 은 release 경유 후 `--no-ff`

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
