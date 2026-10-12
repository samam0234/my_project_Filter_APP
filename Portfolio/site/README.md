# 포트폴리오 사이트 (Next.js)

컷앤킵을 설명하는 화면이다. 제품 `frontend/`와는 다른 앱이다.

```bash
cd Portfolio/site
npm install
npm run dev
```

주소는 `http://127.0.0.1:5190` 이다.

안내 챗은 같은 오리진의 `/api/chat`이 `PORTFOLIO_AI_URL`(기본 `http://127.0.0.1:5055`) Flask로 넘긴다.
화면의 챗 기록은 브라우저 `localStorage` 키 `cnk-portfolio-chat-v1` 이다. 학습 예시는 안내 서비스의 `data/rag_memory.json`과 `data/chroma`에 남는다.
깊이 추론 횟수는 `GET /api/deep`가 안내 서비스 `GET /v1/deep`를 읽는다. 파일은 `Portfolio/ai/data/deep_quota.sqlite`다. 브라우저와 사이트 함수 디스크에는 횟수를 저장하지 않는다. 보내면 바로 줄고, 안내 서비스가 요청을 받은 뒤에는 되돌리지 않는다. 한국 시간 오전 12시 전에는 10으로 다시 채워지지 않는다.
