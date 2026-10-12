# 안내 검색에 Chroma 문단 추가 / `2296005`

> 브랜치: `feature/chroma-portfolio`  
> 작성일: `2026-10-12 20:15`  
> 작성자: `agent`  
> 파일명: `261012_2015_2296005_guide-chroma_feature-chroma-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(portfolio): 안내 검색에 Chroma 문단 추가` |
| **커밋 번호 (SHA)** | `22960059874c7ee3ff1b6b331c049b86b05cb40e` |
| **짧은 SHA** | `2296005` |
| **브랜치** | `feature/chroma-portfolio` |
| **부모 커밋** | `4d816a1` |

## 2. 주 커밋 내용

- 안내 마크다운 조각을 `Portfolio/ai/data/chroma` 컬렉션 `guide_docs`에 둔다.
- 배운 질문과 답은 JSON과 컬렉션 `guide_memory`에 같이 남긴다.
- BM25로 고른 문단 뒤에, 아직 없는 가까운 문단을 최대 두 개 더한다.
- 화면 대화 목록은 localStorage다. 임베딩 모델은 받지 않는다.
- 설명 페이지와 약관에서 벡터 저장소가 없다는 문장을 고친다.

## 3. 상세 내용

### 3.1 배경 / 목적
안내 문장이 문서 밖 사실을 만들지 않도록, 질문과 글자가 가까운 문단을 근거에 더한다.

### 3.2 변경 범위
- 추가된 경로: `Portfolio/ai/chroma_embed.py`, `Portfolio/ai/chroma_store.py`, `Portfolio/ai/test_chroma_store.py`, `Portfolio/ai/data/chroma/`
- 수정된 경로: `guide_graph.py`, `rag_memory.py`, `requirements.txt`, 안내 README, 마크다운 04·05·07·08, 사이트 AI·백엔드·챗·약관·ERD 문장
- 삭제된 경로: 없음

### 3.3 기술 포인트
문서가 바뀌지 않으면 색인을 다시 만들지 않는다. Chroma를 열지 못하면 기존 BM25와 JSON 검색만 쓴다. 의존성은 `chromadb==1.5.9`.

### 3.4 의도적으로 하지 않은 것
제품 모델 변경, Ollama pull, 화면 기록의 서버 저장, 배포.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [x] API/UI 스모크
- 결과 서술: `test_chroma_store.py` 통과. `guide_graph`가 문서 184개를 읽는다. 개발 서버에서 `/ai`, `/backend`, `/chat`, `/terms`, `/data/erd` HTML에 Chroma 문장이 있다. 브라우저 클릭 흐름은 보지 않았다.

### 4.2 부작용 / 리스크
첫 질문은 문서 색인을 만든다. 글자 벡터라 말만 바꾸고 글자가 거의 안 겹치는 질문은 여전히 놓칠 수 있다.

### 4.3 후속 작업
세 파트를 develop에 순서대로 병합한 뒤 검토하고 main에 병합한다.

### 4.4 관련 문서
- `Portfolio/ai/README.md`
- `Portfolio/markdown/05-ai.md`
