# 포트폴리오 안내 (Flask)

제품 FastAPI와 별도다. 사진을 처리하지 않고, 데이터베이스에 연결하지 않는다.

- LangGraph: 이해 → 검색 → 초안 → 문서와 어긋나면 한 번 수정
- LangChain: `ChatPromptTemplate`, `StrOutputParser`, `ChatOllama`, 문서 검색기
- 검색: BM25와 글자 2-gram, 제목 일치, 말투를 고유명사로 바꾸는 확장. 벡터 DB 없음
- 모델: Ollama `gemma4:12b`. 생각 토큰은 끄고, 문맥은 6144토큰
- 기록: 없음. 브라우저가 최근 대화를 요청마다 다시 보낸다

```bash
cd Portfolio/ai
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python app.py
```

상태: `GET http://127.0.0.1:5055/health`  
질문: `POST http://127.0.0.1:5055/v1/guide` body `{ "messages": [{ "role": "user", "content": "..." }] }`

`gemma4:12b`가 없으면 health가 503이다. 이 서비스가 제품의 기본 해석 모델(`gemma4:e4b`)을 바꾸지는 않는다.
