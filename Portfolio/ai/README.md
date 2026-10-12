# 포트폴리오 안내 (Flask)

제품 FastAPI와 별도다. 사진을 처리하지 않고, 데이터베이스에 연결하지 않는다.

- LangGraph: 이해 → 검색 → 초안 → 필요하면 수정 → 학습 JSON 저장
- LangChain: `ChatPromptTemplate`, `StrOutputParser`, `ChatOllama`, 문서 검색기, 비슷한 질문 생성
- 검색: 문서 BM25와 글자 2-gram, `data/chroma`의 문서 벡터, 그리고 `data/rag_memory.json`의 배운 대화. 임베딩 모델은 받지 않는다
- 모델: 기본 Ollama `gemma4:e4b`. 보내기 위 버튼으로 `gemma4:12b`를 고른다. 일반 답은 생각 토큰을 끄고 문맥 6144, 생성 800이다
- 깊이 추론 횟수: `data/deep_quota.sqlite`. 한국 시간 날짜가 바뀌기 전에는 줄인 횟수를 되돌리지 않는다. `GET /v1/deep`
- 깊이 추론: 요청의 `deep`이 참이면 검색·문맥·생성을 2.5배로 한다. 생각 토큰은 켜지 않는다. 켜면 그 한도를 생각만 쓰고 본문이 비기 때문이다. 하루 10번은 이 파일에서 센다
- 화면 기록: 브라우저 localStorage. 이 Flask는 데이터베이스에 연결하지 않는다
- 학습: 답이 문서에 맞게 나오면 질문, 비슷한 질문, 답을 `data/rag_memory.json`과 `data/chroma`에 남긴다. 다음 비슷한 질문의 보완 예시로만 쓴다

```bash
cd Portfolio/ai
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python app.py
```

상태: `GET http://127.0.0.1:5055/health`  
질문: `POST http://127.0.0.1:5055/v1/guide` body `{ "messages": [{ "role": "user", "content": "..." }] }`

기본 모델 `gemma4:e4b`가 없으면 health가 503이다. `gemma4:12b`가 없어도 기본 답은 된다. 이 서비스가 제품의 기본 해석 모델을 바꾸지는 않는다.
