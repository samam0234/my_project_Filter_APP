# 해석기 비교 — 혼합(LoRA 먼저 · 갈리면 Ollama)이 지금 체인보다 정확 · 빠름, PROMPT_SECOND_OPINION 로 켤 수 있게 / `bbfc671cc09252c9f51f34d4d6d515f7813d0212`

> 브랜치: `feature/parser-compare`  
> 작성일: `2026-10-09 16:40`  
> 작성자: `agent`  
> 파일명: `261009_1640_bbfc671_parser-compare_feature-parser-compare.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(llm): 해석기 비교 — 혼합(LoRA 먼저 · 갈리면 Ollama)이 지금 체인보다 정확 · 빠름, PROMPT_SECOND_OPINION 로 켤 수 있게` |
| **커밋 번호 (SHA)** | `bbfc671cc09252c9f51f34d4d6d515f7813d0212` |
| **짧은 SHA** | `bbfc671` |
| **브랜치** | `feature/parser-compare` |
| **부모 커밋** | `9af96bb` |

## 2. 주 커밋 내용

- 해석기 비교 스크립트 · 결과(253문장)
- `PROMPT_SECOND_OPINION` 설정 (체인 재질문 provider 분리)

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "LoRA 는 기본이 아니고 체인과 같은 조건 비교를 안 함" 보완.

### 3.2 변경 범위
- 추가: `scripts/experiments/parser_compare.py`, `docs/vaildates/parser-compare-20261009.md` · 원자료
- 수정: `backend/app/services/prompt_chain.py`, `config.py`, `.env.example`, `tests/unit/test_prompt_chain.py`, llm-and-vision · FEATURES · 색인

### 3.3 기술 포인트
- LoRA greedy → 같은 provider 재질문은 같은 답 → 두 번째 의견은 다른 provider 여야 투표 의미가 있음

### 3.4 의도적으로 하지 않은 것
- 기본 LLM_PROVIDER 변경, Docker 이미지에 transformers 추가

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 437 통과
- [x] 혼합 91.3% · 3.0초 vs 기본 85.4% · 6.9초

### 4.2 부작용 / 리스크
- 없음 (기본값 그대로)

### 4.3 후속 작업
- 승인된 실제 문장으로 재비교 후 GPU 서버 기본값 결정

### 4.4 관련 문서
- `docs/vaildates/parser-compare-20261009.md`
