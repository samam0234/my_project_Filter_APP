# Portfolio/site — 컷앤킵 설명 사이트 (Next.js)

> 컷앤킵을 장별로 읽는 화면과, 안내 챗을 Flask로 이어 주는 작은 API.

제품 `frontend/`와는 **다른 앱**이다. 컷앤킵 기능을 실행하지 않고 설명만 한다.

| 항목 | 내용 |
|------|------|
| 공개 주소 | https://cutnkeep-portfolio.vercel.app (Vercel) |
| 로컬 주소 | http://127.0.0.1:5190 |
| 기술 | Next.js 15 (App Router) · React 19 · TypeScript 5.9 |
| 안내 연결 | 같은 오리진의 `/api/chat` · `/api/deep` → Flask 안내 ([`../ai/`](../ai/README.md)) |

---

## 1. 화면

| 경로 | 내용 | 원고 |
|------|------|------|
| `/` | 소개 · 목차 · 프로젝트와 기능 요약 | `markdown/01-overview.md` |
| `/frontend` | 사용자 앱 · 화면 캡처 | `02-frontend.md` |
| `/console` | 운영 콘솔 · 검수 | `03-console.md` |
| `/backend` | FastAPI 서버 | `04-backend.md` |
| `/ai` | 비전 · 문장 해석 · 학습 | `05-ai.md` |
| `/project` | 사업 · 업무 관점의 소개 | `06-project.md` |
| `/terms` | 이 사이트의 이용약관 | `07-terms.md` |
| `/data/erd` | ERD — 원본 HTML을 프레임으로 (`public/erd/`) | `08-erd.md` |
| `/data/spreadsheet` | 스프레드시트 10개 시트 — 빌드 때 `../assets/spreadsheet.json`을 읽음 | `09-spreadsheet.md` |
| `/chat` | **안내 챗** | — |

화면 캡처는 `public/shots/`, 공통 틀은 `components/Shell.tsx`(머리글 · 내비게이션) · `ReadingBar.tsx`(읽기 진행) · `GuideStatus.tsx`(안내 연결 상태)다.

---

## 2. 안내 챗

```text
브라우저 (/chat)
  ├─ 대화 기록 → localStorage "cnk-portfolio-chat-v1"
  └─ POST /api/chat ─▶ PORTFOLIO_AI_URL (Flask) /v1/guide
     GET  /api/chat ─▶ /health            (연결 상태)
     GET  /api/deep ─▶ /v1/deep           (깊이 추론 남은 횟수)
```

| 항목 | 내용 |
|------|------|
| 모델 버튼 | 보내기 위 버튼은 `gemma4:e4b`와 `gemma4:12b`만 **고른다.** 그 버튼은 전송하지 않는다 |
| 깊이 추론 | 뇌 버튼을 선택한 뒤 보내기나 왼쪽 추천 질문으로 전송한다. 보내면 남은 횟수가 바로 줄어든다 |
| 0회 | 뇌 버튼은 눌리지 않고, 마우스를 올리면 `토큰 횟수가 전부 떨어졌으니 자정때 까지 기다려주시길 바랍니다.` |
| 제한 시간 | 챗 함수 `maxDuration`은 300초 (Vercel Hobby 한도). 대기는 일반 160초 · 깊이 추론 290초 |

깊이 추론 횟수는 **Flask가 센다.** `GET /api/deep`가 `GET /v1/deep`만 읽고, 이 사이트는 횟수를 브라우저에도 함수 디스크에도 저장하지 않는다.

- 안내에 닿지 않으면 남은 횟수를 10으로 만들지 않는다.
- 같은 날짜에서 더 큰 남은 횟수가 오면 화면은 무시한다.
- 한국 시간 오전 12시 전에는 10으로 다시 채워지지 않는다.

사이트 함수의 임시 디스크(`/tmp`)에 두면 인스턴스가 바뀔 때 10으로 보이기 때문에 거기에 쓰지 않는다.

---

## 3. 구조

```text
site/
├── app/
│   ├── layout.tsx · page.tsx · globals.css
│   ├── frontend/ console/ backend/ ai/ project/ terms/    장별 페이지
│   ├── data/erd/ · data/spreadsheet/                       데이터 장 (SheetView)
│   ├── chat/                                               ChatPanel · page
│   └── api/
│       ├── chat/route.ts       GET 상태 · POST 질문 → Flask
│       └── deep/route.ts       GET 남은 깊이 추론 횟수
├── components/                 Shell · ReadingBar · GuideStatus
├── lib/deepQuota.ts            Flask /v1/deep 읽기
├── public/                     erd/ · shots/ · favicon
└── next.config.ts · tsconfig.json · package.json
```

---

## 4. 실행

```bash
cd Portfolio/site
npm install
npm run dev          # http://127.0.0.1:5190
```

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 (5190) |
| `npm run build` | 프로덕션 빌드 |
| `npm run start` | 빌드 결과 실행 (5190) |

| 환경변수 | 기본 | 설명 |
|----------|------|------|
| `PORTFOLIO_AI_URL` | `http://127.0.0.1:5055` | Flask 안내 주소. 공개 배포에서는 터널 주소 |

Flask 안내가 꺼져 있어도 페이지는 모두 열린다. 챗만 "안내 서비스에 연결하지 못했습니다"를 보여 준다.

---

## 5. Vercel 배포

| 설정 | 값 |
|------|----|
| 프로젝트 | `cutnkeep-portfolio` |
| Root Directory | `Portfolio/site` |
| Node | 22.x |
| 루트 밖 파일 포함 | 켬 — `/data/spreadsheet`가 `../assets/spreadsheet.json`을 읽는다 |
| 환경변수 | `PORTFOLIO_AI_URL` (production) |

이 Vercel 계정은 GitHub 로그인 연결이 없어 Git 자동 배포 대신 CLI로 올린다.
저장소 전체는 파일이 많아 느리므로 `Portfolio/site`와 `Portfolio/assets`만 같은 구조로 복사한 폴더에서 `npx vercel deploy --prod`를 실행한다.
`node_modules` · `.next` · `site/data`는 빼되 **`app/data`는 빼지 않는다** (빠지면 `/data/erd` · `/data/spreadsheet`가 404).

전체 순서: [`../README.md` 6절](../README.md#6-공개-배포-2026-10-12-기준)
