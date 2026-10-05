# 학습 데이터 검수(승인·삭제)와 회원 요청 후보 수집 / `723176153f0d0cad68cb5902da96b4323adf83d2`

> 브랜치: `feature/feedback-review`  
> 작성일: `2026-10-06 03:13`  
> 작성자: `agent`  
> 파일명: `261006_0313_7231761_learning-review-console_feature-feedback-review.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(console): 학습 데이터 검수(승인·삭제)와 회원 요청 후보 수집` |
| **커밋 번호 (SHA)** | `723176153f0d0cad68cb5902da96b4323adf83d2` |
| **짧은 SHA** | `7231761` |
| **브랜치** | `feature/feedback-review` |
| **부모 커밋** | `7f4aec7` (feature/db-split) |

## 2. 주 커밋 내용

- 운영 콘솔 "학습 데이터" 페이지 + API: 승인 · 정답 고쳐서 승인 · 거절 · 되돌리기 · 일괄 · 삭제
- 로그인 회원 요청(문장 + 시스템 해석)을 검수 후보(`request`)로 수집
- RAG 는 **승인된** 샘플만 사용

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 점검 4번: 사용자 교정이 바로 RAG 에 들어가 잘못된 교정이 모든 사용자에게 퍼질 수 있었다 → 승인 관문.
또 "사용자의 프롬프트로 학습" 요청에 맞춰 실제 회원 요청 문장을 학습 데이터 후보로 모은다.

### 3.2 변경 범위

- 추가: `backend/app/services/learning_review.py`, `backend/app/schemas/learning.py`,
  `console/src/pages/LearningPage.tsx`, `tests/unit/test_learning_review.py`
- 수정: `backend/app/{core/config.py, main.py, models/learning_sample.py, routers/{console,upload}.py,
  services/{learning_catalog,prompt_rag}.py}`, `console/src/{App.tsx, api/client.ts, components/Sidebar.tsx, types/index.ts}`,
  `training/lora/eval_parser.py`, `tests/unit/{conftest,test_prompt_rag}.py`, `.env.example`,
  `docs/{API_DOCUMENTATION.md, guidance/{console-admin,llm-and-vision}.md, plan/DATABASE.md}`

### 3.3 기술 포인트

- 삭제 = 원본 사이드카 삭제 + 피드백 행 삭제 + 샘플 `deleted` 표식(내용 비움). 표식이 없으면 기동 동기화가 되살림
- 회원 요청 후보는 같은 문장 1건만, cp949 깨진 문장 제외, 업로드 실패를 막지 않도록 예외는 로그만
- RAG 색인 서명 = 승인 샘플 수 + 최종 수정 시각 → 승인·삭제가 30 s 안에 반영
- 이미지 엔드포인트는 학습 데이터·업로드 폴더 안의 파일만 (경로 조작 방지)

### 3.4 의도적으로 하지 않은 것

- 콘솔 로그인 (기존대로 loopback 제한)
- 회원 요청 수집 동의 UI — 운영 공개 전 이용약관·안내 필요 (후속)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 실서버(MariaDB): 기동 백필로 기존 요청 9건 후보화(깨진 문장 2건 제외), 승인 → RAG 색인 1건,
      비슷한 표현 "왼쪽에서 두번째 사람 지워 줘" 검색 점수 0.63 → 되돌리기로 원상 복구
- [x] 콘솔 `npm run build` 통과
- [x] pytest 전체 통과 (신규 8건, RAG 테스트 3건 교체)

### 4.2 부작용 / 리스크

- 이제 교정은 승인 전까지 RAG 에 쓰이지 않음 (즉시 반영 → 검수 후 반영)
- 기존 안전모·조끼 요청 2건은 옛 해석(selector 없음)이 후보 정답 → 검수 시 고쳐서 승인 필요

### 4.3 후속 작업

- 승인 데이터로 LoRA 학습 (`train_lora --source db`) · 데이터 증강

### 4.4 관련 문서

- `docs/guidance/console-admin.md` (학습 데이터 검수)
