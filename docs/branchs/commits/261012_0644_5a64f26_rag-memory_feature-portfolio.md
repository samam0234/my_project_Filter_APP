# 안내 챗 학습 예시를 JSON에 저장 / `5a64f26358476c8b950f57bfa9a6e300b1229dec`

> 브랜치: `feature/portfolio`  
> 작성일: `2026-10-12 06:44`  
> 작성자: `agent`  
> 파일명: `261012_0644_5a64f26_rag-memory_feature-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(portfolio): 안내 챗 학습 예시를 JSON에 저장` |
| **커밋 번호 (SHA)** | `5a64f26358476c8b950f57bfa9a6e300b1229dec` |
| **짧은 SHA** | `5a64f26` |
| **브랜치** | `feature/portfolio` |
| **부모 커밋** | `40f8392ee48a35eb0402ab7f117bf83aaa9950c3` |

## 2. 주 커밋 내용

- 안내 답이 만들어지면 질문, 비슷한 질문, 답을 `Portfolio/ai/data/rag_memory.json`에 남김
- 비슷한 다음 질문은 그 예시를 문서 옆 보완으로 사용. 문서와 다르면 문서를 따름
- 거의 같은 질문은 새 항목으로 늘리지 않고 말투만 합침
- 화면 대화 목록은 계속 브라우저 localStorage. 데이터베이스는 쓰지 않음
- 학습 JSON은 Git에 올리지 않음

## 3. 상세 내용

### 3.1 배경 / 목적

문서 검색만으로는 한 번 설명한 말투와 빠진 점을 다음 질문에 잇기 어려웠기 때문.

### 3.2 변경 범위

- 추가: `Portfolio/ai/rag_memory.py`
- 수정: 안내 그래프, Flask 설명, 챗·약관·AI·ERD 문구, `.gitignore`

### 3.3 기술 포인트

- LangGraph 마지막 노드 `remember`가 짧은 생성으로 같은 뜻의 질문 3개를 만듦
- 검색은 BM25와 글자 2-gram. 항목은 최대 200개

### 3.4 의도적으로 하지 않은 것

- develop/main 병합, push
- 화면 기록을 서버에 저장
- 학습 JSON 커밋

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 「오픈 보캐브」 질문 후 JSON에 비슷한 질문 4개가 저장됨
- [x] 「열린 어휘」로 다시 물으면 근거에 `rag_memory.json`이 포함됨
- [ ] Docker 확인 — 해당 없음

### 4.2 부작용 / 리스크

학습 JSON이 틀린 답을 남기면 다음 비슷한 질문에 그 표현이 섞일 수 있다. 문서가 우선이다.

### 4.3 후속 작업

develop 병합은 사용자가 시킬 때만 한다.

### 4.4 관련 문서

- `Portfolio/ai/README.md`
- `Portfolio/markdown/05-ai.md`
