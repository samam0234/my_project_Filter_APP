# Grounding DINO + SAM2 오픈 보캐브 실가동 확인 기록 / `2d7cab957c41b077e754a0765a359849925d0710`

> 브랜치: `feature/open-vocab-check`  
> 작성일: `2026-10-07 12:10`  
> 작성자: `agent`  
> 파일명: `261007_1207_2d7cab9_open-vocab-check_feature-open-vocab-check.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(vaildates): Grounding DINO + SAM2 오픈 보캐브 실가동 확인 기록` |
| **커밋 번호 (SHA)** | `2d7cab957c41b077e754a0765a359849925d0710` |
| **짧은 SHA** | `2d7cab9` |
| **브랜치** | `feature/open-vocab-check` |
| **부모 커밋** | `feature/celery-worker` 끝 (기록 커밋) |

## 2. 주 커밋 내용

- DINO tiny · SAM2 tiny 가중치를 로컬 HF 캐시에 준비
- COCO 밖 대상 shirt · helmet 이 `dino_sam2` 로 처리됨을 확인, person 은 yolo 유지
- 결과·주의점을 `docs/vaildates/open-vocab-20261007.md` 에 기록

## 3. 상세 내용

### 3.1 배경 / 목적
인수인계 남은 일 "DINO/SAM2 가중치 + 활성화"를 확인.

### 3.2 변경 범위
- 추가: `docs/vaildates/open-vocab-20261007.md`
- 수정: `docs/vaildates/README.md`
- 코드 변경 없음 (기능은 이미 구현돼 있었고 가중치만 없었음)

### 3.3 기술 포인트
- 로더는 `local_files_only` 라 가중치는 미리 받아야 함
- `OPEN_VOCAB_ENABLED` 기본값 false 유지

### 3.4 의도적으로 하지 않은 것
- 정답 기반 정확도 평가·임계값 튜닝, 시작 시 워밍업 구현
- Docker GPU 이미지 반영

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬(training/.venv, CUDA) 확인 — person 8.6s(yolo) / shirt 16.4s(첫 로드) / helmet 0.8s
- 결과 서술: `docs/vaildates/open-vocab-20261007.md`

### 4.2 부작용 / 리스크
- 이미지에 없는 대상(helmet)도 검출될 수 있음(오검출 가능성)

### 4.3 후속 작업
- 임계값 평가, 워밍업, 총 병합

### 4.4 관련 문서
- `docs/vaildates/open-vocab-20261007.md`
