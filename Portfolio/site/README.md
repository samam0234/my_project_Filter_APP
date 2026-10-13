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
깊이 추론 횟수는 `GET /api/deep`가 안내 서비스 `GET /v1/deep`를 읽는다. 파일은 `Portfolio/ai/data/deep_quota.sqlite`의 표 `deep_day`다. 날짜는 UTC+9다. 브라우저와 사이트 함수 디스크에는 횟수를 저장하지 않는다. 안내에 닿지 않으면 남은 횟수를 10으로 만들지 않는다. 보내면 바로 줄고, 안내 서비스가 요청을 받은 뒤에는 되돌리지 않는다. 한국 시간 오전 12시 전에는 10으로 다시 채워지지 않는다. 남은 횟수가 0이면 뇌 버튼은 눌리지 않고, 안내 문장은 `토큰 횟수가 전부 떨어졌으니 자정때 까지 기다려주시길 바랍니다.`다.
보내기 위 버튼은 `gemma4:e4b`와 `gemma4:12b`만 고른다. 그 버튼은 전송하지 않는다. 챗 함수 `maxDuration`은 300이고, 대기는 일반 160초, 깊이 추론 290초다.
