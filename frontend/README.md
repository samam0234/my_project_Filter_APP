# frontend — 컷앤킵 사용자 웹 앱

> 사진 · 움직이는 GIF · 짧은 영상을 올리고, **한 문장**으로 대상만 남기거나 지우는 화면.

일반 사용자가 쓰는 React 앱이다. 운영자용 화면은 여기가 아니라 [`console/`](../console/README.md)(포트 5174)다.
이 앱은 백엔드의 `/api/v1`과 `/health`만 호출하고 데이터베이스에 직접 붙지 않는다.

| 항목 | 내용 |
|------|------|
| 로컬 주소 | http://localhost:5173 (Vite가 `/api` · `/health`를 `localhost:8000`으로 넘김) |
| Docker | nginx가 80번에서 정적 파일을 주고 같은 경로를 `backend:8000`으로 프록시 |
| 공개 화면 | Cloudflare Worker `cutnkeep-front` — 정적 파일 + `/api` 프록시 ([`deploy/`](../deploy/README.md)) |
| 기술 | React 18 · TypeScript 5 · Vite 7 · Tailwind CSS 3 · Zustand 4 · axios · react-dropzone · lucide-react · Pretendard |
| 테스트 | Vitest + Testing Library + jsdom · **95개** (2026-10-12) |
| Node | **22.12 이상** (`package.json` `engines`) |

---

## 1. 이 앱이 하는 일

사용 흐름은 세 단계다.

```text
1 올리기          2 문장                          3 처리
사진 · GIF · 영상 → "가운데 사람만 남기고 배경 블러" → 해석 칩 확인 → 원본/결과 비교 → 저장 · 평가
```

처리가 끝나면 화면은 AI가 문장을 어떻게 이해했는지 **"이렇게 이해했어요"** 칩으로 보여 준다(대상 · 위치 · 개수 · 색 · 효과).
해석이 틀렸다면 회원은 **정답 알려주기**로 고친 해석을 보낼 수 있고, 운영자가 검수한 정답은 다음 해석의 예시가 된다.

### 비로그인과 회원

화면은 이 차이를 기준으로 설계했다.

| | 비로그인 | 회원 |
|--|---------|------|
| 작업실 처리 | 결과 저장(다운로드)만. **서버에 남지 않고** 새로고침하면 사라짐. 원본은 브라우저 미리보기 | 저장 · 작업 상세 링크 · 평가 · 정답 알려주기 |
| 홈 "최근 작업" | 로그인 안내 | 내 최근 작업 4건 |
| 작업 기록 · 상세 · 배치 | 로그인 게이트 | 본인 것만 |
| 영상 | 마지막 결과 1개를 이 브라우저(IndexedDB)에 보관 — 유일한 사본 | 서버에도 24시간 보관, 작업 기록 링크 |

회원 전용 화면에는 메뉴에 자물쇠가 붙고, 비로그인이 들어오면 `RequireLogin` 게이트가 로그인 · 가입 안내를 보여 준다. 로그인하면 `?next=`로 원래 화면에 돌아간다.

---

## 2. 화면

| 경로 | 화면 | 내용 | 쓰는 API |
|------|------|------|----------|
| `/` | 홈 | 소개 · **원본/결과 비교 데모**(SVG, 키보드로 움직이는 손잡이) · 예시 문장 칩 · 할 수 있는 것 · 사용 순서 · 최근 작업 | `GET /jobs?limit=4` |
| `/studio` | **작업실** | 탭 **사진 · GIF**(`?type=gif`) · 단계(1 업로드 · 2 문장 · 3 처리) · 진행 막대 · 해석 칩 · Before/After · 결과 저장(GIF는 WebP도) · 평가 | `POST /upload` · `POST /gif` · `POST /feedback` |
| `/video` | 영상 | 짧은 영상 처리 · 바로 재생 · mp4 저장 · 마지막 결과 IndexedDB 보관 · 회원은 작업 기록 링크 | `POST /video` · `GET /video/{id}` |
| `/batch` 🔒 | 배치 | 같은 문장으로 최대 500장 · 진행률 · 항목별 원본/결과 · zip 받기 · 내 배치 | `POST /batch` · `GET /batch/{id}` |
| `/account` 🔒 | 내 계정 | `?tab=` 구역: 내 정보(표시 이름 · 이용 현황) / 작업 기록 / 보안(비밀번호 변경 · 전체 로그아웃) / 보관 · 탈퇴 | `GET /jobs` · `PATCH /auth/me` · `POST /auth/password/change` · `POST /auth/logout-all` · `DELETE /auth/me` |
| `/account?tab=history` 🔒 | 작업 기록 | 본인 작업(사진 · 영상 · GIF) 최근 120건 · 종류 · 상태 필터 · 문장 검색(URL 쿼리 유지). 예전 `/history`는 여기로 이동 | `GET /jobs?limit=120` |
| `/jobs/:id` 🔒 | 작업 상세 | 결과(영상은 재생) · 해석 JSON 복사 · 메타 · 평가 · 정답 알려주기 · 같은 문장으로 다시 작업 | `GET /jobs/{id}` · `POST /feedback` |
| `/guide` | 프롬프트 가이드 | 남기기 vs 지우기 · 위치 / 크기 / 순서 / 개수 / 색 고르기 · 예시 · 한계 | — |
| `/guide?tab=agent` | **에이전트에게 묻기** | AI 채팅. 원하는 결과를 말하면 요청 문장을 추천하고 "작업실에서 써 보기"로 채움 · 답변 모델 선택 | `POST /chat` |
| `/login` | 로그인 | 아이디 · 비밀번호, `?next=`, 아이디 / 비밀번호 찾기 링크 | `POST /auth/login` |
| `/signup` | 가입 ① | 입력 즉시 규칙 안내 · **[필수] 만 14세 · 약관 · 처리방침 동의** → 이메일로 일련번호 발송 | `POST /auth/signup/start` |
| `/signup/verify` | 가입 ② | 메일의 8글자 일련번호 입력(하이픈 자동) · 다시 받기 · 성공하면 바로 로그인 | `POST /auth/signup/verify` · `/signup/resend` |
| `/find-id` | 아이디 찾기 | 가입 이메일로 아이디 발송 (가입 여부와 관계없이 같은 안내) | `POST /auth/find-id` |
| `/find-password` | 비밀번호 찾기 | ① 아이디 + 이메일 → 코드 ② 코드 + 새 비밀번호 | `POST /auth/password/request` · `/reset` |
| `/privacy` · `/terms` | 처리방침 · 약관 | 운영자 정보는 `src/data/legal.ts` (빌드 인자 `VITE_OPERATOR_*`) | — |
| 그 외 | 404 | | |

🔒 = 회원 전용.

**머리글** 오른쪽의 점은 백엔드 상태다. `GET /health`를 30초마다 불러 초록이면 연결되어 있다. 그 옆은 계정 메뉴다 (비로그인: 로그인 · 가입 / 회원: 프로필 버튼 → 내 계정 · 작업 기록 · 배치 · 로그아웃).

### 가입 흐름

```text
/signup  정보 입력 + 동의 ──▶ 메일로 8글자 일련번호 ──▶ /signup/verify 입력 ──▶ 계정 생성 · 로그인
```

- 일련번호는 30분 유효, 5회까지 시도, 다시 받기는 60초 간격이다.
- 동의(만 14세 이상 · 이용약관 · 개인정보 처리방침)는 서버도 다시 검사하고 동의 시각을 남긴다.
- 입력 규칙은 백엔드와 같은 규칙을 화면에도 둬서 제출 전에 알려 준다.

자세히: [`docs/guidance/auth.md`](../docs/guidance/auth.md)

### 해석 모델 고르기

작업실의 처리하기 옆 상자에서 Ollama `gemma4:e4b`(기본) · `gemma4:12b` · `qwen3.8:27b`를 고른다.

- 서버에 설치되지 않은 모델은 **"미적용"** 으로 표시되고 고를 수 없다 (`GET /llm/models`).
- 고른 값은 이 브라우저(localStorage)에 남는다.
- 서버가 LoRA로 해석하는 구성이면 이 상자는 숨는다. 배치는 서버 기본 모델만 쓴다.

### "정답 알려주기" → 학습

결과 아래 **정답 알려주기**는 서버 해석(`parsed_prompt`)을 미리 채운 폼을 연다 (대상 · 하고 싶은 것 · 위치 · 몇 번째 · 개수 · 색 · 부위 · 블러 강도 · 크롭).
고친 값은 `ParsedPrompt` JSON으로 싫어요 피드백에 실려 가고, 운영 콘솔에서 승인되면 RAG 예시와 LoRA 학습 정답이 된다 (`training/lora/dataset.comment_as_parsed`).

---

## 3. 구조

```text
frontend/
├── src/
│   ├── main.tsx · App.tsx      진입점 · 경로 → 페이지 · 문서 제목
│   ├── router.tsx              History API 기반 최소 라우터
│   ├── api/client.ts           axios → /api/v1 (요청별 제한 시간)
│   ├── pages/                  Home · Studio · Video · Batch · Account · JobDetail · Guide · NotFound
│   │   ├── auth/               Login · Signup · SignupVerify · FindId · FindPassword
│   │   └── legal/              처리방침 · 약관
│   ├── components/
│   │   ├── layout/             AppLayout — 내비게이션 · 서버 상태 · 푸터 · 좁은 화면 펼침 메뉴
│   │   ├── home/               HeroDemo — 원본/결과 비교 데모
│   │   ├── image/              드롭존 · Before/After · 진행 상태 · ResultImage(투명 체크무늬)
│   │   ├── gif/                GifWorkspace — 작업실 GIF 탭
│   │   ├── prompt/             입력 · 예시 칩 · ParsedPromptView(해석 칩)
│   │   ├── feedback/           좋아요 / 싫어요 + 정답 알려주기
│   │   ├── chat/               AgentChat — 에이전트에게 묻기
│   │   ├── account/            내 계정 구역
│   │   ├── auth/               AuthForm · RequireLogin
│   │   ├── jobs/               JobCard
│   │   └── common/             Button · PageHeader · Step · StatusBadge · 로딩 / 에러 / 빈 상태
│   ├── store/                  Zustand — 작업실 · 계정 · 채팅 · 해석 모델
│   ├── hooks/                  useImageProcessing · useFeedback · useApi
│   ├── data/                   examples.ts(공용 예시 문장) · legal.ts(운영자 정보)
│   ├── utils/                  formatters.ts(한국어 라벨 · 날짜) · videoStore.ts(IndexedDB)
│   └── types/
├── index.html · index.css      Tailwind · 디자인 토큰
├── tailwind.config.ts          brand 색 · Pretendard · 그림자
├── vite.config.ts              dev 5173 · 프록시
├── nginx.conf · Dockerfile     Docker 서빙 · 보안 헤더
└── vitest.config.ts · vitest.setup.ts
```

| 영역 | 경로 | 설명 |
|------|------|------|
| 라우터 | `src/router.tsx` | `usePathname` · `navigate` · `matchRoute` · `Link`. 새로고침 · 직접 접근은 Vite dev 서버와 `nginx.conf`의 `try_files … /index.html`이 처리 |
| 작업실 상태 | `src/store/useAppStore.ts` | 입력 · 결과를 페이지를 옮겨도 유지 |
| 계정 상태 | `src/store/useAuthStore.ts` | `/auth/me` 결과. 세션 토큰은 HttpOnly 쿠키라 JS에 없다 |
| 채팅 · 모델 | `src/store/useChatStore.ts` · `useLlmModelStore.ts` | 채팅 대화(새로고침하면 사라짐) · 고른 해석 모델(localStorage) |
| 회원 게이트 | `src/components/auth/RequireLogin.tsx` | 회원 전용 화면 감싸기 (loading · 안내 · children) |
| 다음 주소 | `src/components/auth/AuthForm.tsx` `safeNext` | `?next=`가 `/`로 시작하고 `//`가 아닐 때만 따라간다 (외부 주소로 튕기지 않게) |
| 영상 보관 | `src/utils/videoStore.ts` | 마지막 영상 결과를 IndexedDB에 |

### 라우팅 라이브러리를 쓰지 않은 이유

화면 수에 비해 경로 파라미터가 적어 약 50줄의 라우터로 충분하고, 의존성과 lockfile을 늘리지 않기 위해서다.

### API 연결과 제한 시간

| 호출 | 제한 시간 |
|------|-----------|
| 기본 | 30초 |
| 사진 처리 `POST /upload` · 채팅 `POST /chat` | 300초 |
| GIF `POST /gif` · 영상 `POST /video` | 600초 |
| 배치 등록 `POST /batch` · 결과 파일 받기 | 120초 |
| 모델 목록 · `/auth/me` | 8초 · `/health` 5초 |

Cloudflare Worker를 거치면 약 100초에서 응답이 끊긴다. 긴 영상 · GIF · 큰 해석 모델은 서버 직접 주소가 더 여유가 있고(약 300초), 화면은 그 경우를 안내만 한다.

비로그인 처리 응답은 파일을 저장하지 않고 data URL로 돌아와 화면이 바로 내려받게 한다.
AI 채팅은 서버에 대화를 쌓지 않는다. 화면이 최근 대화를 요청마다 보내고, 서버는 답만 돌려준다.

---

## 4. 디자인

다크 테마를 유지하고 완성도를 올렸다 (밝은 테마 전환은 하지 않았다).

| 원칙 | 구현 |
|------|------|
| 한국어 줄바꿈 | `word-break: keep-all` — 낱말 중간에서 끊기지 않게 |
| 글꼴 | Pretendard를 빌드에 포함. 외부 CDN을 쓰지 않는다 (CSP와도 맞음) |
| 디자인 토큰 | `tailwind.config.ts` brand 색 스케일, `src/index.css`의 `card` · `field` · `eyebrow` · `step-dot` |
| 접근성 | 키보드 초점 링, 움직임 줄이기(`prefers-reduced-motion`) 설정을 따른다 |
| 좁은 화면 | 1024px 미만은 아이콘만이 아니라 **메뉴 이름이 보이게** 펼친다. 페이지를 옮기면 메뉴는 닫힌다 |
| 데모 그림 | 홈 비교 데모는 실제 인물 사진이 아니라 SVG — 저작권과 초상권 때문 |

2026-10-08 확인에서 데스크톱 1440과 모바일 390 모두 가로 스크롤이 없었다. 캡처는 `docs/vaildates/ui-design-20261008-*.jpg`.

### 보안 헤더 (nginx)

`nginx.conf`가 모든 응답에 붙인다: CSP(스크립트는 같은 출처만, 인라인 금지) · `X-Content-Type-Options: nosniff` · `X-Frame-Options: DENY` · `Referrer-Policy` · `Permissions-Policy`. `server_tokens off`로 버전을 숨긴다.
백엔드 주소는 Docker DNS로 10초마다 다시 찾는다. 백엔드 컨테이너가 다시 만들어져 IP가 바뀌어도 502가 나지 않게 하기 위해서다 ([`docs/repeater/nginx-backend-502.md`](../docs/repeater/nginx-backend-502.md)).

---

## 5. 실행

```bash
cd frontend
npm install      # 최초 1회
npm run dev      # http://localhost:5173
```

- 백엔드(:8000)가 떠 있어야 처리와 결과가 동작한다. 첫 처리는 모델 로드로 시간이 걸릴 수 있다.
- 화면만 확인할 때는 백엔드 없이도 뜬다 (머리글의 점이 회색).

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 |
| `npm run build` | 타입 검사(`tsc -b`) + 프로덕션 빌드 → `dist/` |
| `npm run preview` | 빌드 미리보기 |
| `npm run test` | Vitest 한 번 실행 (95개) |
| `npm run test:watch` | 바뀐 파일만 다시 실행 |
| `npm run lint` | ESLint |

### 운영 빌드 (처리방침 표기)

개인정보 처리방침 · 약관의 운영자 정보는 **빌드할 때 박힌다.** 바꾸면 다시 빌드해야 한다.

```bash
VITE_OPERATOR_NAME="컷앤킵 운영자" VITE_OPERATOR_EMAIL="<문의 메일>" VITE_POLICY_DATE="2026-10-11" npm run build
```

Docker는 `.env`의 `OPERATOR_NAME` · `OPERATOR_EMAIL` · `POLICY_DATE` · `FEEDBACK_IMAGE_RETENTION_DAYS`를 빌드 인자로 넘긴다. 서버와 Cloudflare Worker의 화면 번들 이름(`assets/index-*.js`)이 같은지 배포 후 확인한다.

### 테스트

```bash
npx tsc --noEmit && npx vitest run
```

영상 · 배치 · GIF · 내 계정 · 가입 인증 · AI 채팅 · 머리글 메뉴 · 입력 규칙 · API 클라이언트 · 포맷터 · IndexedDB 보관(`fake-indexeddb`)을 다룬다.

---

## 6. 알려진 한계와 다음 일

- Cloudflare 경유 시 긴 영상 · GIF · 큰 해석 모델이 약 100초에서 끊긴다. 화면은 안내만 한다.
- 실제 휴대폰과 실제 메일함의 가입 버튼은 미검증으로 남아 있다.
- 접근성 자동 점검 도구는 돌리지 않았다.
- AI 채팅 스트리밍은 없다. 답을 한 번에 받는다.
- 이메일 주소 변경과 기존 회원의 이메일 재인증은 없다.
- 로컬에서는 5173과 5174가 쿠키를 공유한다 (쿠키는 포트를 구분하지 않는다). 콘솔에 관리자로 로그인하면 같은 브라우저의 사용자 앱도 그 계정이 된다. 다른 계정 시험은 시크릿 창으로.

예정: 마스크를 COCO · YOLO-seg 형식으로 내려받기 · 브라우저 안에서 ONNX로 처리해 서버에 사진을 보내지 않는 경로 · 채팅 응답 나누어 받기.

---

## 관련 문서

- [`docs/guidance/user-frontend.md`](../docs/guidance/user-frontend.md) — 사용 흐름
- [`docs/guidance/auth.md`](../docs/guidance/auth.md) — 계정 · 가입 인증 · 메일
- [`docs/guidance/llm-and-vision.md`](../docs/guidance/llm-and-vision.md) — 프롬프트 규격 (selector · remove_object)
- [`docs/guidance/cloudflare-deploy.md`](../docs/guidance/cloudflare-deploy.md) — 화면을 Cloudflare Worker로
- [`docs/API_DOCUMENTATION.md`](../docs/API_DOCUMENTATION.md) · [`docs/Architecture/apps.md`](../docs/Architecture/apps.md)
- [`RUN.md`](../RUN.md)
