# 비전 기본 m 과 ONNX·Vite 스택 문서를 코드에 맞춤 / `351eaa785084224cd7324e6e833e1d7d23441323`

> 브랜치: `feature/docs-sync`  
> 작성일: `2026-10-06 22:26`  
> 작성자: `agent`  
> 파일명: `261006_2226_351eaa7_plan-docs-align_feature-docs-sync.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(plan): 비전 기본 m 과 ONNX·Vite 스택 문서를 코드에 맞춤` |
| **커밋 번호 (SHA)** | `351eaa785084224cd7324e6e833e1d7d23441323` |
| **짧은 SHA** | `351eaa7` |
| **브랜치** | `feature/docs-sync` |
| **부모 커밋** | `1306ed16a06484286fe9f16836f4c1fe810d3239` |

## 2. 주 커밋 내용

- `AI_MODEL_STRATEGY.md` 상단·결론의 s 스케일 표기를 YOLO26m-seg 기준으로 정리
- `CURRENT_STACK.md` 스냅샷을 2026-10-06 로 갱신 (ONNX 슬림 이미지, Vite 7 / Vitest 5)
- `LOGIC_STRUCTURE.md` §3.1 을 "예정"에서 현재 `backend/app/` 경로로 교체. SAM2 는 Phase 2 로 남김

## 3. 상세 내용

### 3.1 배경 / 목적

남은 작업 인수인계의 문서 불일치를 코드와 맞춘다. Phase 2 기능은 시작하지 않는다.

### 3.2 변경 범위

- 수정: `docs/plan/AI_MODEL_STRATEGY.md`, `docs/plan/CURRENT_STACK.md`, `docs/plan/LOGIC_STRUCTURE.md`
- 추가·삭제: 없음

### 3.3 기술 포인트

- 서빙 기본은 `config.py` 의 `models/yolo26m-seg.pt`. 학습 출발 가중치는 s-seg 유지
- ONNX 추론은 구현됨 (`onnx_utils.py`). 하드코딩 미구현으로 적지 않음

### 3.4 의도적으로 하지 않은 것

- Phase 2 (SAM2, Celery, 영상)
- develop / main 병합, push, 배포
- pytest · Docker ONNX 재기동 (이번 커밋 범위 밖)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [ ] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 문서만 수정. 테스트·컨테이너는 돌리지 않음.

### 4.2 부작용 / 리스크

- 없음 (문서)

### 4.3 후속 작업

- 사용자가 파트를 끝내라고 하면 다른 feature 와 함께 `--no-ff` 총 병합
- 테스트·Docker ONNX 검증은 별도 지시 후

### 4.4 관련 문서

- `docs/plan/YOLO26M_DEFAULT.md`
- `docs/plan/ONNX_INFERENCE.md`
