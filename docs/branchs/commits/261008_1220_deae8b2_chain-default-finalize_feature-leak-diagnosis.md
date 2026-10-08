# 해석 체인을 기본값으로 — LLM 답과 키워드 파서 다수결, 공급자 정보 보존, 검증 문서 최종화 / `deae8b254488ae711d0d0c8be637147092538836`

> 브랜치: `feature/leak-diagnosis`  
> 작성일: `2026-10-08 12:20`  
> 작성자: `agent`  
> 파일명: `261008_1220_deae8b2_chain-default-finalize_feature-leak-diagnosis.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(prompt): 해석 체인을 기본값으로 — LLM 답과 키워드 파서 다수결, 공급자 정보 보존, 검증 문서 최종화` |
| **커밋 번호 (SHA)** | `deae8b254488ae711d0d0c8be637147092538836` |
| **짧은 SHA** | `deae8b2` |
| **브랜치** | `feature/leak-diagnosis` |
| **부모 커밋** | `c806f1d` |

## 2. 주 커밋 내용

- `PROMPT_CHAIN` 기본값을 `langchain` 으로 변경 (처음 보는 30문장 대상 정확도 86.7% → 96.7%, LLM 호출 평균 1.4번)
- 체인에 `ask` 주입 — 테스트가 실제 Ollama 를 호출하지 않음
- LangChain 이 컨텍스트를 복사해 사라지던 성공 provider 이름을 상태에 담아 `set_last_llm_provider` 로 호출 측에 복원
- 배치·영상 경로(`parse_prompt_or_heuristic`)도 같은 체인 사용
- 학습 루프 문서·`.env.example` 반영, 검증 문서 최종본과 문장 해석 라운드 원자료 JSON 추가

## 3. 상세 내용

### 3.1 배경 / 목적
체인의 효과가 확인되어 기본값으로 전환하고, 사진·배치·영상이 같은 해석 경로를 쓰게 맞춤.

### 3.2 변경 범위
- 추가: `docs/vaildates/parse_rounds_20261008.json`, `parse_rounds_fresh_20261008.json`
- 수정: `config.py`, `.env.example`, `prompt_chain.py`, `prompt_llm.py`, `workflows/nodes.py`, `learning-loop.md`, 검증 문서·README 색인, `test_prompt_chain.py`

### 3.3 기술 포인트
- provider 메타데이터가 ContextVar 로만 전달돼 체인 안에서 유실 → 상태 필드로 전달
- LLM 이 꺼져 있으면(provider 가 LLM 아님) 체인을 쓰지 않고 키워드 파서로 폴백

### 3.4 의도적으로 하지 않은 것
- LoRA 재학습 실행, RAG 지식 베이스 채우기(승인 샘플이 없음), 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 pytest 371 통과
- [x] Docker 백엔드 재빌드, 시스템 상태에서 chain=langchain·votes=3·겹침 subtract·GrabCut/CLAHE 끔 확인
- 사진 종단 확인(Docker 업로드 API)은 최종 보고에 별도 기재

### 4.2 부작용 / 리스크
- 키워드 파서와 갈릴 때만 LLM 을 더 부르므로 평균 지연은 소폭 증가(호출 1.4배)
- 문장 수치는 30문장 표본이라 신뢰구간이 넓음

### 4.3 후속 작업
- 사용자 승인 후 병합, LoRA 재학습(`python scripts/retrain_lora.py --force`)

### 4.4 관련 문서
- `docs/guidance/learning-loop.md`, `docs/vaildates/leak-diagnosis-20261008.md`
