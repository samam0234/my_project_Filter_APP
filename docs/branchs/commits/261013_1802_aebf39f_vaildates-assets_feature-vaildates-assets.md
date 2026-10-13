# 검증 원자료와 이미지를 폴더로 나눔 / `aebf39f`

> 브랜치: `feature/vaildates-assets`  
> 작성일: `2026-10-13 18:02`  
> 작성자: `agent`  
> 파일명: `261013_1802_aebf39f_vaildates-assets_feature-vaildates-assets.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(vaildates): 검증 원자료와 이미지를 폴더로 나눔` |
| **커밋 번호 (SHA)** | `aebf39fda897110e48215d8656b006e3228d4dcf` |
| **짧은 SHA** | `aebf39f` |
| **브랜치** | `feature/vaildates-assets` |
| **부모 커밋** | `4a8f51b` |

## 2. 주 커밋 내용

- `docs/vaildates`의 JSON 34개를 `json_files/`로 옮겼다.
- 비교 이미지 11개를 `images/`로 옮겼다.
- 마크다운은 같은 폴더에 두었다.
- 문서 링크와 실험 스크립트 예시 출력 경로를 새 폴더로 맞췄다.

## 3. 상세 내용

### 3.1 배경 / 목적
검증 기록이 마크다운, JSON, 이미지가 한 폴더에 섞여 있었다. 원자료와 그림만 전용 폴더로 나누고, 글은 그대로 두기 위해서다.

### 3.2 변경 범위
- 추가된 경로: `docs/vaildates/json_files/`, `docs/vaildates/images/`
- 수정된 경로: `docs/vaildates/*.md` 중 원자료를 가리키던 글, `scripts/experiments/`의 예시 `--out` 경로
- 삭제된 경로: 없음. 파일은 이름 그대로 하위 폴더로 이동했다

### 3.3 기술 포인트
이동은 `git mv`라 이력은 따라간다. 실험 수치는 고치지 않았다. COCO 주석 `instances_val2017.json`처럼 이 폴더 밖 파일 이름은 그대로 두었다.

### 3.4 의도적으로 하지 않은 것
실험 결론 재작성, 과거 커밋 기록의 당시 경로 수정, 테스트 재실행, 제품 배포.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 마크다운의 상대 링크가 `json_files/`와 `images/` 안의 파일을 가리키는지 경로로 확인했다. 실험을 다시 돌리지는 않았다.

### 4.2 부작용 / 리스크
예전에 적은 커밋 기록은 옮기기 전 경로를 말한다. 지금 위치는 `docs/vaildates/README.md`와 각 글의 링크를 따른다.

### 4.3 후속 작업
이 브랜치 기록 커밋 뒤 develop, main 순서로 병합한다.

### 4.4 관련 문서
- `docs/vaildates/README.md`
