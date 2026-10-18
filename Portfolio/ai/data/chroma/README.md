# Portfolio/ai/data/chroma — 안내 챗의 문서 · 기억 벡터

> 포트폴리오 안내 챗(Flask)이 쓰는 Chroma 저장소. 제품 백엔드와는 관계없다.

| 컬렉션 | 내용 |
|--------|------|
| `guide_docs` | 안내 문서 조각 — `Portfolio/markdown/*.md`와 핵심 제품 문서(`docs/HANDOVER.md` · `FEATURES.md` · `WORKFLOW.md`) |
| `guide_memory` | 배운 질문과 답 — 답이 문서에 맞게 나왔을 때 질문 · 비슷한 질문 · 답을 남긴다 (`rag_memory.json`과 같이) |

- 임베딩 모델은 받지 않는다. 글자 벡터를 쓴다.
- **화면의 대화 목록은 여기 없다.** 브라우저 `localStorage`에만 있다.
- 실행 파일은 Git에 올리지 않는다. 안내 서비스가 문서가 바뀌면 다시 맞춘다. 위치는 `PORTFOLIO_CHROMA_DIR`로 바꿀 수 있다.

검색은 문서 BM25 + 글자 2-gram에 이 저장소의 가까운 문단을 더한다. 예시와 문서가 다르면 문서를 따른다 → [`Portfolio/ai/README.md`](../../README.md)
