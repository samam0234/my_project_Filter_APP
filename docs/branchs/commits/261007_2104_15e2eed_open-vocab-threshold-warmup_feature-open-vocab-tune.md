# 오픈 보캐브 전용 임계값·빈 라벨 박스 제거·기동 워밍업 / `15e2eed54f431f93750c7edc5b5a99c099bfdb9c`

> 브랜치: `feature/open-vocab-tune`  
> 작성일: `2026-10-07 21:04`  
> 작성자: `agent`  
> 파일명: `261007_2104_15e2eed_open-vocab-threshold-warmup_feature-open-vocab-tune.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(segmentation): 오픈 보캐브 전용 임계값·빈 라벨 박스 제거·기동 워밍업` |
| **커밋 번호 (SHA)** | `15e2eed54f431f93750c7edc5b5a99c099bfdb9c` |
| **짧은 SHA** | `15e2eed` |
| **브랜치** | `feature/open-vocab-tune` |
| **부모 커밋** | `f50f97e` |

## 2. 주 커밋 내용

- 설정 `OPEN_VOCAB_BOX_THRESHOLD`(0.35) · `OPEN_VOCAB_TEXT_THRESHOLD`(0.25) 추가 — YOLO `MIN_CONFIDENCE` 와 분리
- `_keep_matched`: 라벨이 빈(문구와 이어지지 않은) DINO 박스 제거
- `warmup_open_vocab`: `PRELOAD_MODELS` 워밍업에서 DINO·SAM2 도 미리 로드 (`OPEN_VOCAB_ENABLED` 일 때만)
- 테스트 3건(빈 라벨 제거, 임계값 분리, 꺼져 있을 때 워밍업 생략), `.env.example` 안내

## 3. 상세 내용

### 3.1 배경 / 목적
`2d7cab9` 실가동 확인에서 "helmet" 이 헬멧 없는 사진에서 2개 검출됐다. 원인을 보니 DINO 후처리 임계값이 YOLO 용 `MIN_CONFIDENCE`(0.25)를 박스·문구 모두에 쓰고 있었다. 또 첫 요청이 모델 로드로 16초 걸렸다.

### 3.2 변경 범위
- 수정: `backend/app/core/config.py`, `backend/app/services/segmentation.py`, `backend/app/main.py`, `.env.example`, `tests/unit/test_phase2.py`

### 3.3 기술 포인트
- 기본값은 Grounding DINO 공식 권장(box 0.35 / text 0.25). COCO 정답 기반 측정 결과는 같은 브랜치의 후속 문서 커밋에 기록
- 워밍업은 빈 이미지에 "object" 로 한 번 추론 — 실패해도 경고만, 첫 요청에서 다시 시도

### 3.4 의도적으로 하지 않은 것
- 요청별 임계값 조절 UI

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과

### 4.2 부작용 / 리스크
- 임계값을 올려 작은·흐린 대상은 덜 잡힐 수 있음 → 측정으로 확인

### 4.3 후속 작업
- COCO 정답 기반 임계값 측정 문서 (`docs/vaildates/open-vocab-20261007.md` 갱신)

### 4.4 관련 문서
- `docs/vaildates/open-vocab-20261007.md`
