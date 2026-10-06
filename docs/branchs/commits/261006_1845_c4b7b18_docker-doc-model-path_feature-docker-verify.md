# Docker 안내의 세그 가중치를 설정 기준으로 정정 / `c4b7b1832c3e7c20eaba882cc2272f91881407ab`

> 브랜치: `feature/docker-verify`  
> 작성일: `2026-10-06 18:45`  
> 작성자: `agent`  
> 파일명: `261006_1845_c4b7b18_docker-doc-model-path_feature-docker-verify.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(docker): Docker 안내의 세그 가중치를 설정 기준으로 정정` |
| **커밋 번호 (SHA)** | `c4b7b1832c3e7c20eaba882cc2272f91881407ab` |
| **짧은 SHA** | `c4b7b18` |
| **브랜치** | `feature/docker-verify` |
| **부모 커밋** | `10d20af` (feature/docker-verify) |

## 2. 주 커밋 내용

- `docs/guidance/docker-run.md`: 세그 가중치 안내를 `yolo26s-seg.pt` 고정 → `YOLO_MODEL_PATH`(기본 m) 기준
- 점검 표에 s · m CPU 세그 시간 함께

## 3. 상세 내용

### 3.1 배경 / 목적

같은 작업 묶음의 `feature/yolo-m` 에서 서빙 모델을 m 으로 바꿨다. 병합 후 develop 에서 직접 고치지 않도록
총 병합 전에 이 브랜치에서 문서를 맞춘다.

### 3.2 변경 범위

- `docs/guidance/docker-run.md`

### 3.3 기술 포인트

- 없음 (문서)

### 3.4 의도적으로 하지 않은 것

- 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 문서 표기 확인

### 4.2 부작용 / 리스크

- 없음

### 4.3 후속 작업

- 총 병합

### 4.4 관련 문서

- `docs/plan/YOLO26M_DEFAULT.md`
