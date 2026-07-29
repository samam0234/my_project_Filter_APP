# 하드코딩·바이브 구간 구분선 정리 / `a783ee76fa2df1b9b6784214c6bdd4582ad54602`

> 브랜치: `feature/hardcoding-zones`  
> 작성일: `2026-07-29 17:35`  
> 작성자: `agent`  
> 파일명: `260729_1735_a783ee7_hardcoding-vibe-zones_feature-hardcoding-zones.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(hardcoding): 하드코딩·바이브 구간 구분선 정리` |
| **커밋 번호 (SHA)** | `a783ee76fa2df1b9b6784214c6bdd4582ad54602` |
| **짧은 SHA** | `a783ee7` |
| **브랜치** | `feature/hardcoding-zones` |
| **부모 커밋** | `26e0bb778bafa15431ac8e1f4a5f35e208989247` |

## 2. 주 커밋 내용

- `[하드코딩 파트]` / `[이미 구현된 구간 · 바이브]` 구분선 통일
- `# >>> 여기에 작성 <<<` 커서 위치 표시
- 휴리스틱·YOLO·stub 등 완료 코드에 바이브 마커
- `HARDCODING_ZONES.md` 표시 규칙 동기화

## 3. 상세 내용

### 3.1 배경 / 목적

하드코딩 주석과 이미 구현된 코드가 붙어 보이던 문제를 줄이고,  
작업 구간을 시각적으로 분리한다.

### 3.2 변경 범위

- 수정:
  - `backend/app/workflows/nodes.py`, `edges.py`
  - `backend/app/services/segmentation.py`
  - `backend/app/utils/onnx_utils.py`
  - `backend/app/tasks/batch_tasks.py`
  - `backend/app/core/config.py`
  - `training/lora/train_lora.py`
  - `scripts/evaluate_model.py`, `fine_tune_lora.py`, `pseudo_labeling.py`
  - `docs/plan/HARDCODING_ZONES.md`

### 3.3 기술 포인트

- 블록 경계: `# =============` 긴 구분선
- 하드코딩 블록 직후 바이브 fallback/stub 유지 (런타임 동작 동일)

### 3.4 의도적으로 하지 않은 것

- LLM·ONNX·배치·LoRA 본문 구현
- 원격 푸시, develop 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과

- 주석·문서 정리만. 런타임 로직 변경 없음.

### 4.2 부작용 / 리스크

- 주석 형식 변경으로 diff 가 커 보일 수 있음.

### 4.3 후속 작업

- (선택) `git push -u origin feature/hardcoding-zones`
- develop 병합 시 `--no-ff`

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
