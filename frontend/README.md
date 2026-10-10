# frontend — 사용자 웹 앱

일반 사용자가 **사진 · 움직이는 GIF · 짧은 영상을 올리고 한 문장으로 배경을 지우거나, 특정 대상만 남기거나 지우는** React 앱이다.
운영 관리 UI는 여기가 아니라 **`console/`** (포트 5174) 이다.

## 페이지

| 경로 | 페이지 | 내용 | 쓰는 API |
|------|--------|------|----------|
| `/` | 홈 | 소개 · **원본/결과 비교 데모**(SVG) · 예시 칩 · 할 수 있는 것 · 사용 순서 · 최근 작업 4건 | `GET /jobs?limit=4` |
| `/studio` | **작업실** | 카테고리 탭 **사진 · GIF**(`?type=gif`) · 단계(1 업로드 · 2 문장 · 3 처리) · 처리 진행 막대 · 해석 칩 · Before/After · 결과 저장(GIF 는 WebP 도) · 평가 | `POST /upload`, `POST /gif`, `POST /feedback` |
| `/account` | 내 계정 🔒 | 헤더 프로필 메뉴로 진입 · `?tab=` 구역: 내 정보(표시 이름 수정 · 이용 현황) / 작업 기록 / 보안(비밀번호 변경 · 전체 로그아웃) / 보관 · 탈퇴 | `GET /jobs`, `PATCH /auth/me`, `POST /auth/password/change`, `POST /auth/logout-all`, `DELETE /auth/me` |
| `/account?tab=history` | 작업 기록 🔒 | **본인 작업**(사진 · 영상 · GIF) 최근 120건 · 종류 필터 · 상태 필터 · 프롬프트 검색 (URL 쿼리 유지). 예전 `/history` 는 여기로 이동 | `GET /jobs?limit=120` |
| `/jobs/:id` | 작업 상세 🔒 | 결과(영상은 재생) · 해석 JSON 복사 · 메타 · 평가/정답 알려주기 · 같은 문장으로 다시 작업 | `GET /jobs/{id}`, `POST /feedback` |
| `/guide` | 프롬프트 가이드 | 남기기 vs 지우기 · 위치/크기/순서/개수/색 고르기 · 예시(누르면 작업실로) · 한계 | — |
| `/batch` | 배치 🔒 | 여러 장 등록 · 진행률 · 항목별 원본/결과 · zip 받기 · 내 배치 | `POST /batch`, `GET /batch/{id}` |
| `/video` | 영상 | 짧은 영상 처리 · 바로 재생 · mp4 저장 · 이 브라우저(IndexedDB)에 마지막 결과 보관 · 회원은 작업 기록 링크 | `POST /video`, `GET /video/{id}` |
| `/login` | 로그인 | 아이디·비밀번호, `?next=` 로 돌아갈 곳, 아이디/비밀번호 찾기 링크 | `POST /auth/login` |
| `/signup` | 회원가입 | 입력 즉시 규칙 안내, **[필수] 만 14세 · 약관 · 방침 동의**, 가입 후 바로 로그인 | `POST /auth/signup` |
| `/find-id` | 아이디 찾기 | 가입 이메일로 아이디 발송 (항상 같은 안내) | `POST /auth/find-id` |
| `/find-password` | 비밀번호 찾기 | ① 아이디+이메일 → 코드 ② 코드+새 비밀번호 | `POST /auth/password/request`, `/reset` |
| `/privacy` · `/terms` | 개인정보 처리방침 · 이용약관 | 운영자 정보는 `src/data/legal.ts`(빌드 인자 `VITE_OPERATOR_*`) | — |
| 그 외 | 404 | | |

🔒 = 로그인 회원 전용. 비로그인이 들어오면 `RequireLogin` 게이트가 로그인·회원가입 안내를 보여주고
(로그인 후 `next` 로 복귀), 메뉴에도 자물쇠가 붙는다.

상단 내비게이션 우측 점은 백엔드 상태(`GET /health`, 30초마다), 그 옆은 계정 메뉴다
(비로그인: 로그인·회원가입 / 로그인: 이름 → 작업 기록, 로그아웃).

### 비로그인 vs 회원

| | 비로그인 | 회원 |
|--|---------|------|
| 작업실 | 처리 후 **결과 저장(다운로드)만** — 서버에 남지 않고 새로고침하면 사라짐. 원본은 브라우저 미리보기 | 저장 · 작업 상세 링크 · 평가/정답 알려주기 |
| 홈 "최근 작업" | 로그인 안내 | 내 최근 작업 4건 |
| 작업 기록 · 상세 · 배치 | 게이트 | 본인 것만 |

계정 상세: `docs/guidance/auth.md`

## "정답 알려주기" → LoRA 학습

결과 아래 **정답 알려주기**는 서버 해석(`parsed_prompt`)을 미리 채운 폼을 연다
(대상 · 하고 싶은 것 · 위치 · 몇 번째 · 개수 · 색·부위 · 블러 강도 · 크롭).
사용자가 고친 값은 `ParsedPrompt` JSON 으로 **dislike 코멘트**에 실려 가고,
`training/lora/dataset.comment_as_parsed` 가 이를 다음 LoRA 학습의 정답으로 쓴다.

## 구조

| 영역 | 경로 | 설명 |
|------|------|------|
| 라우터 | `src/router.tsx` | History API 기반 최소 라우터 (`usePathname`, `navigate`, `matchRoute`, `Link`) |
| 루트 | `src/App.tsx` | 경로 → 페이지, 문서 제목 |
| 페이지 | `src/pages/` | Home · Studio · History · JobDetail · Guide · Batch · Video · NotFound |
| 레이아웃 | `src/components/layout/AppLayout.tsx` | 내비게이션(1024px 미만은 펼침 메뉴) · 서버 상태 · 푸터 |
| 홈 데모 | `src/components/home/HeroDemo.tsx` | 원본/결과 비교 데모 (SVG 그림, 키보드 조작 손잡이) |
| GIF | `src/components/gif/GifWorkspace.tsx` | 작업실 GIF 탭 (업로드 · 처리 · 결과 · WebP) |
| 이미지 | `src/components/image/` | 드롭존, Before/After(영상 재생 · 추가 다운로드 지원), 진행 상태, `ResultImage`(투명 체크무늬) |
| 프롬프트 | `src/components/prompt/` | 입력, 예시 칩, `ParsedPromptView`(해석 칩) |
| 피드백 | `src/components/feedback/FeedbackPanel.tsx` | 좋아요/싫어요 + 정답 알려주기 |
| 작업 | `src/components/jobs/JobCard.tsx` | 썸네일 카드 |
| 공통 | `src/components/common/` | Button(`buttonClass`), PageHeader, Step(단계 머리), StatusBadge, 로딩/에러/빈 상태 |
| 디자인 토큰 | `tailwind.config.ts`, `src/index.css` | brand 색 · Pretendard · `card` · `field` · `eyebrow` · `step-dot` |
| 상태 | `src/store/useAppStore.ts` | 작업실 입력·결과 (페이지를 옮겨도 유지) |
| 계정 상태 | `src/store/useAuthStore.ts` | `/auth/me` 결과 (세션 토큰은 HttpOnly 쿠키라 JS 에 없음) |
| 계정 화면 | `src/pages/auth/`, `src/components/auth/AuthForm.tsx` | 로그인·가입·찾기, 입력 규칙(백엔드와 동일), `safeNext` |
| 회원 게이트 | `src/components/auth/RequireLogin.tsx` | 회원 전용 화면 감싸기 (loading · 안내 · children) |
| API | `src/api/client.ts` | axios → backend `/api/v1` (업로드 180s · 영상·GIF 600s) |
| 훅 | `src/hooks/` | `useImageProcessing`, `useFeedback(jobId)`, `useApi`(jobs·job·health) |
| 데이터 | `src/data/examples.ts` | 홈·작업실·가이드 공용 예시 프롬프트 |
| 포맷 | `src/utils/formatters.ts` | 점수·크기·날짜(UTC→로컬)·효과/위치/클래스 한국어 라벨 |
| 영상 보관 | `src/utils/videoStore.ts` | 마지막 영상 결과를 IndexedDB 에 |

라우팅 라이브러리를 추가하지 않은 이유: 페이지 6개에 파라미터 1개라 50줄 라우터로 충분하고,
의존성·lockfile 을 늘리지 않기 위해서다. 새로고침·직접 접근은 Vite dev 서버와
`nginx.conf`(`try_files … /index.html`)가 처리한다.

## 실행

```powershell
cd frontend
npm install   # 최초 1회
npm run dev
```

- URL: http://localhost:5173
- Vite 프록시: `/api`, `/health` → `http://localhost:8000`
- 백엔드가 떠 있어야 처리·결과가 동작한다 (첫 처리는 모델 로드로 30초 이상 걸릴 수 있음)

## 스크립트

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 |
| `npm run build` | 타입 검사(`tsc -b`) + 프로덕션 빌드 |
| `npm run preview` | 빌드 미리보기 |
| `npm run test` | Vitest (50개 — 영상 · 배치 · GIF · 작업 기록 · 입력 등) |

## 관련 문서

- `docs/guidance/user-frontend.md` — 사용 흐름
- `docs/guidance/llm-and-vision.md` — 프롬프트 규격 (selector · remove_object)
- `docs/API_DOCUMENTATION.md`
- `docs/Architecture/apps.md`
- `RUN.md`
