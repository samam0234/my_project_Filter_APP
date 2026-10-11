# 포트폴리오 사이트 (Next.js)

컷앤킵을 설명하는 화면이다. 제품 `frontend/`와는 다른 앱이다.

```bash
cd Portfolio/site
npm install
npm run dev
```

주소는 `http://127.0.0.1:5190` 이다.

안내 챗은 같은 오리진의 `/api/chat`이 `PORTFOLIO_AI_URL`(기본 `http://127.0.0.1:5055`) Flask로 넘긴다.
챗 기록은 브라우저 `localStorage` 키 `cnk-portfolio-chat-v1` 이다.
