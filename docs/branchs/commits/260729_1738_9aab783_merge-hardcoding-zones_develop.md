# feature/hardcoding-zones → develop 병합 (no-ff) / `9aab78320ad918dba73dbc734018e00827d2f5ef`

> 브랜치: `develop`  
> 작성일: `2026-07-29 17:38`  
> 작성자: `agent`  
> 파일명: `260729_1738_9aab783_merge-hardcoding-zones_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/hardcoding-zones into develop (no-ff)` |
| **커밋 번호 (SHA)** | `9aab78320ad918dba73dbc734018e00827d2f5ef` |
| **짧은 SHA** | `9aab783` |
| **브랜치** | `develop` |
| **부모 커밋** | `6e570cb` (develop), `90b63f8` (feature tip) |

## 2. 주 커밋 내용

- `feature/hardcoding-zones` 를 develop 에 **no-ff** 병합
- 하드코딩 주석·바이브 구분선·`HARDCODING_ZONES.md` 통합
- feature 쪽 branchs 커밋 기록 3건 포함

## 3. 상세 내용

### 3.1 배경 / 목적

하드코딩 작업 구간 정리를 통합 브랜치 develop 에 반영.

### 3.2 변경 범위

- 하드코딩/바이브 주석: nodes, segmentation, onnx_utils, batch_tasks, config, edges
- 스크립트·LoRA 스캐폴드 주석
- `docs/plan/HARDCODING_ZONES.md`
- `docs/branchs/commits/*hardcoding*`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수)
- 런타임 로직 변경 없음 (주석·문서 중심)

### 3.4 의도적으로 하지 않은 것

- main 병합
- origin 푸시 (요청 시)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 로컬 develop 이 origin/develop 보다 앞서 있음 (병합 + feature 커밋들)

### 4.2 부작용 / 리스크

- 없음에 가까움

### 4.3 후속 작업

- (선택) `git push origin develop`
- (선택) `git push -u origin feature/hardcoding-zones`

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
- `docs/guidance/branch-merge.md`
