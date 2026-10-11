# 안내 챗 검색과 답변 그래프 강화 / `c772fa83ca1e6c4b1de3b562a84ad45ae3f8894d`

> 브랜치: `feature/portfolio`  
> 작성일: `2026-10-12 06:25`  
> 작성자: `agent`  
> 파일명: `261012_0625_c772fa8_guide-graph_feature-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(portfolio): 안내 챗 검색과 답변 그래프 강화` |
| **커밋 번호 (SHA)** | `c772fa83ca1e6c4b1de3b562a84ad45ae3f8894d` |
| **짧은 SHA** | `c772fa8` |
| **브랜치** | `feature/portfolio` |
| **부모 커밋** | `8e135c1a03eaa3b9dbd2b0154540d5ac3a127e80` |

## 2. 주 커밋 내용

- `Portfolio/ai` 안내를 LangGraph 네 단계로 바꿈. 이해, 검색, 초안, 필요하면 한 번 수정
- 검색은 BM25, 글자 2-gram, 제목 일치, 말투를 고유명사로 펼치는 확장
- 같은 파일이 결과를 독점하지 않게 하고, HANDOVER와 FEATURES에 가중치를 둠
- 짧은 이어 질문은 직전 사용자 질문을 검색에 합침
- 초안에 문서 밖 숫자, 없는 예정, 파일 이름이 있으면 한 번 다시 씀
- gemma4:12b는 생각 토큰을 끄고 문맥 6144, 답 상한 800토큰
- 사이트 프록시 대기 시간을 160초로 늘림

## 3. 상세 내용

### 3.1 배경 / 목적

답이 한 줄로 끊기거나 파일 이름을 답 안에 붙였다.
검색 조각이 한 문서에 몰리고, 모델 문맥이 짧아 질문이 잘리기 쉬웠기 때문.

### 3.2 변경 범위

- 수정: `Portfolio/ai/guide_graph.py`, `Portfolio/ai/README.md`, `Portfolio/site/app/api/chat/route.ts`
- 제품 FastAPI, `.env`, 기본 모델 `gemma4:e4b`는 그대로

### 3.3 기술 포인트

- LangChain `ChatPromptTemplate`와 `StrOutputParser`가 초안과 수정에 각각 연결됨
- 벡터 데이터베이스는 없고, 대화도 저장하지 않음. 브라우저가 최근 대화를 다시 보냄
- 12b가 없으면 챗만 503

### 3.4 의도적으로 하지 않은 것

- develop/main 병합, push, 배포
- 외부 Gemini API 연결. 안내는 로컬 `gemma4:12b`만 씀
- 모델 자동 다운로드

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 오픈 보캐브, 비로그인/회원, DB 분리, 기본 모델, 콘솔 배포, 가중치 이어 질문을 로컬 12b로 확인
- [x] 답에 `.md` 파일 이름이 남지 않음
- [x] 이어 질문 「가중치는 있나요?」가 오픈 보캐브 가중치로 이어짐
- [ ] Docker 확인 — 해당 없음

### 4.2 부작용 / 리스크

검수가 걸리면 모델 호출이 한 번 더 있어 답까지 수십 초가 더 걸릴 수 있다.
로컬 12b는 호스트형 대형 모델과 문장 힘이 같을 수 없다. 사실 범위는 검색된 문서로 묶는다.

### 4.3 후속 작업

develop 병합은 사용자가 시킬 때만 한다.

### 4.4 관련 문서

- `Portfolio/ai/README.md`
- `docs/HANDOVER.md`
- `docs/FEATURES.md`
