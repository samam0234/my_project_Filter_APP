# 미구현 하드코딩 구간 주석 및 맵 추가 / `bfce56f85768ad8908856163ff1aef8dae5cca4d`

> 브랜치: `feature/hardcoding-zones`  
> 작성일: `2026-07-29 16:59`  
> 작성자: `agent`  
> 파일명: `260729_1659_bfce56f_hardcoding-zones_feature-hardcoding-zones.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(hardcoding): 미구현 하드코딩 구간 주석 및 맵 추가` |
| **커밋 번호 (SHA)** | `bfce56f85768ad8908856163ff1aef8dae5cca4d` |
| **짧은 SHA** | `bfce56f` |
| **브랜치** | `feature/hardcoding-zones` |
| **부모 커밋** | `6e570cb4e54b1cc8edef14477ad37fb6e0885428` |

## 2. 주 커밋 내용

- 미구현·스캐폴드 구간에 통일 하드코딩 주석 형식 적용
- 완성도 부족분 ↔ 작업 위치 맵 문서 추가 (`HARDCODING_ZONES.md`)
- LLM / ONNX / 배치 / LoRA / 의사라벨 / 평가 경로 가이드
- 이미 동작하는 휴리스틱·이펙트·YOLO `.pt` 본선은 미수정

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 스케치상 빈 칸을 개발자가 직접 채울 수 있도록,  
완료 코드에 주석을 덧대지 않고 **미구현 자리만** 임무·연결·규칙·힌트 형식으로 표시한다.

### 3.2 변경 범위

- 추가된 경로:
  - `docs/plan/HARDCODING_ZONES.md`
- 수정된 경로:
  - `backend/app/workflows/nodes.py` — LLM 프롬프트 분석 연결
  - `backend/app/core/config.py` — LLM Settings 안내
  - `backend/app/services/segmentation.py` — ONNX 분기, DINO+SAM2
  - `backend/app/utils/onnx_utils.py` — ONNX 전·후처리 루프
  - `backend/app/tasks/batch_tasks.py` — 배치 실처리 워커
  - `training/lora/train_lora.py` — LoRA 학습 루프
  - `scripts/fine_tune_lora.py`, `pseudo_labeling.py`, `evaluate_model.py`
- 삭제된 경로: 없음

### 3.3 기술 포인트

- 주석 템플릿: `하드코딩 파트 부분 : [작업 이름]` + 임무/연결/규칙/힌트
- 본선 휴리스틱·`_predict_yolo`·effects 는 완료로 간주해 스코프 제외
- 맵 문서에 권장 구현 순서(LLM → ONNX → 평가 → Phase2) 정리

### 3.4 의도적으로 하지 않은 것

- 하드코딩 본문 구현(LLM 호출, ONNX 추론, 배치/LoRA 실학습)
- 휴리스틱 키워드 비우기/재작성
- `develop`/`main` 병합, default 브랜치 변경

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [ ] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 주석·문서 변경만. 런타임 동작 변경 없음(기존 stub/heuristic 유지).

### 4.2 부작용 / 리스크

- 없음에 가까움. 주석 분량 증가로 파일 가독성만 영향.

### 4.3 후속 작업

- 각 하드코딩 파트 본문 구현
- `feature/hardcoding-zones` → `develop` 병합 시 `--no-ff`
- (선택) 원격 푸시

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
- `training/README.md`
- `docs/plan/AI_MODEL_STRATEGY.md`
