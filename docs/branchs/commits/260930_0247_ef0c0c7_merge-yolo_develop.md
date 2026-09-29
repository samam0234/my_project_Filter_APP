# feature/yolo → develop 병합 (no-ff) / `ef0c0c7cc6ea213e35861c3ec7ed43d25a04db23`

> 브랜치: `develop`  
> 작성일: `2026-09-30 02:47`  
> 작성자: `agent`  
> 파일명: `260930_0247_ef0c0c7_merge-yolo_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/yolo into develop (no-ff)` |
| **커밋 번호 (SHA)** | `ef0c0c7cc6ea213e35861c3ec7ed43d25a04db23` |
| **짧은 SHA** | `ef0c0c7` |
| **브랜치** | `develop` |
| **부모 커밋** | `d8e97a7` (develop), `4db0fe8` (feature tip) |

## 2. 주 커밋 내용

- 요청 대상 외 객체가 마스크에 섞이는 필터 수정 (`d4ba085`)

## 3. 상세 내용

### 3.1 배경 / 목적

인스턴스 선택(A~E) 작업이 세 브랜치(`feature/backend`·`feature/llm`·`feature/yolo`) 결과 위에서
진행되어야 하므로, 통합 라인 develop 에 순서대로 no-ff 병합한다.

### 3.2 변경 범위

- 기록: `260930_0153_d4ba085_yolo-target-filter_feature-yolo.md`

### 3.3 기술 포인트

- `git merge --no-ff` (FF 금지 규칙 준수), 병합 순서 backend → llm → yolo
ef0c0c70

### 3.4 의도적으로 하지 않은 것

- 원격 push, main 병합 (release 경유)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 병합 후 pytest 전체 82개 통과 (yolo 병합 시점 기준)

### 4.2 부작용 / 리스크

- 없음 (각 feature 기록의 리스크 참조)

### 4.3 후속 작업

- `feature/instance` 에서 인스턴스 선택 A~E 작업

### 4.4 관련 문서

- `docs/guidance/branch-merge.md`
