# 해석 모델 고르기 반영 — README · 현재 스택 · 배포 · GPU · 테스트 수 / `520ec652c23b0a0daf6ce1b1ce37096af835a2d0`

> 브랜치: `feature/model-select`  
> 작성일: `2026-10-11 03:13`  
> 작성자: `agent`  
> 파일명: `261011_0313_520ec65_docs-model-select_feature-model-select.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 해석 모델 고르기 반영 — README · 현재 스택 · 배포 · GPU · 테스트 수` |
| **커밋 번호 (SHA)** | `520ec652c23b0a0daf6ce1b1ce37096af835a2d0` |
| **짧은 SHA** | `520ec65` |
| **브랜치** | `feature/model-select` |
| **부모 커밋** | `c9092ba` |

## 2. 주 커밋 내용

- 해석 모델 고르기 기능을 문서 전반에 반영 (README · CURRENT_STACK · DEPLOYMENT · gpu-deploy · TESTING · tests README)

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "전반적으로 문서 작업 후 병합하고 푸시".

### 3.2 변경 범위
- 수정: README.md, docs/plan/CURRENT_STACK.md, docs/DEPLOYMENT.md, docs/guidance/gpu-deploy.md, docs/plan/TESTING.md, tests/README.md

### 3.3 기술 포인트
- 모델 고르기는 Ollama 구성에서만 보이고 GPU(LoRA)에서는 숨는다는 점을 두 곳에 명시

### 3.4 의도적으로 하지 않은 것
- 날짜가 붙은 검증 문서의 당시 수치 수정

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 463 · 프론트 65 · 콘솔 21 통과 (문서 등록 검사 포함)

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 모델별 해석 정확도 평가

### 4.4 관련 문서
- `docs/guidance/llm-and-vision.md`
