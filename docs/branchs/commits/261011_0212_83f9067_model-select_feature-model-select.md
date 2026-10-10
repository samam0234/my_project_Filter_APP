# 처리하기 옆에서 문장 해석 모델 고르기 — Ollama e4b · 12b · Qwen 3.8 27b, 설치 안 된 모델은 "미적용" / `83f906709a9a4611ebd3d95e74467c7109a5a641`

> 브랜치: `feature/model-select`  
> 작성일: `2026-10-11 02:12`  
> 작성자: `agent`  
> 파일명: `261011_0212_83f9067_model-select_feature-model-select.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(llm): 처리하기 옆에서 문장 해석 모델 고르기 — Ollama e4b · 12b · Qwen 3.8 27b, 설치 안 된 모델은 "미적용"` |
| **커밋 번호 (SHA)** | `83f906709a9a4611ebd3d95e74467c7109a5a641` |
| **짧은 SHA** | `83f9067` |
| **브랜치** | `feature/model-select` |
| **부모 커밋** | `eda27ea` |

## 2. 주 커밋 내용

- `services/llm_models.py` · `routers/llm.py` (모델 목록 · 확인 · 요청별 적용)
- 사진 · GIF · 영상 `llm_model` 폼 필드, 해석 노드 연결
- `ModelSelect` 컴포넌트와 `useLlmModelStore`, 세 작업실에 배치
- nginx · 프론트 사진 대기 시간 300초

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청: "처리하기 옆에 모델 선택 — ollama e4b · 12b · qwen3.8:27b, 27b 는 다운로드하면 미적용 없애기". 화면에는 기존 선택 기능이 없어 새로 만들었다.

### 3.2 변경 범위
- 추가: `backend/app/services/llm_models.py`, `backend/app/routers/llm.py`, `frontend/src/components/common/ModelSelect.tsx`(+테스트), `frontend/src/store/useLlmModelStore.ts`, `frontend/src/api/client.llmModel.test.ts`, `tests/unit/test_llm_models.py`
- 수정: upload · gif · video 라우터, `workflows/{graph,nodes,state}.py`, `frontend/nginx.conf`, 클라이언트 · 타입 · 세 작업실, 문서

### 3.3 기술 포인트
- 설정 복사본으로 요청별 적용 — 서버 설정은 그대로
- 기본이면 인자를 넘기지 않아 기존 가짜 파이프라인 테스트 15개가 영향받지 않음
- 작업 중 qwen3.8:27b 가 실제로 설치되면서 "미적용이 풀리는" 동작이 실제로 확인됨
- 처음 12b · 27b 호출이 504 — 원인은 nginx 60초, 확인 후 수정

### 3.4 의도적으로 하지 않은 것
- 배치의 모델 선택 (배치 행에 모델을 저장하는 구조 변경 필요)
- 모델별 해석 품질 평가 (e4b 체인 · LoRA 만 비교했음)
- 27b 의 GPU 메모리 문제 해결 (12GB 카드의 한계)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 463 · 프론트 65 통과
- [x] 실제 요청으로 세 모델 모두 처리 확인, 서버가 Ollama 에 보낸 model 직접 확인

### 4.2 부작용 / 리스크
- 27b 는 첫 호출 약 3분 — 화면에 안내하지만 사용자가 기다려야 함
- 큰 모델 요청이 몰리면 GPU 메모리를 오래 점유 (속도 제한이 완화)

### 4.3 후속 작업
- 모델별 해석 정확도 평가 후 기본 모델 재검토, 배치 지원

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md` LLM 절, `docs/guidance/llm-and-vision.md`
