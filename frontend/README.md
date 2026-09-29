# frontend — 사용자 웹 앱

일반 사용자가 **이미지를 올리고 한 문장으로 배경을 지우거나, 특정 대상만 남기거나 지우는** React 앱이다.
운영 관리 UI는 여기가 아니라 **`console/`** (포트 5174) 이다.

## 페이지

| 경로 | 페이지 | 내용 | 쓰는 API |
|------|--------|------|----------|
| `/` | 홈 | 소개 · 할 수 있는 것 · 동작 방식 · 예시 칩 · 최근 작업 4건 | `GET /jobs?limit=4` |
| `/studio` | **작업실** | 업로드 · 프롬프트(예시 칩, Ctrl+Enter) · 처리 진행(경과 시간·단계) · 해석 칩 · Before/After · 결과 저장 · 평가 | `POST /upload`, `POST /feedback` |
| `/history` | 작업 기록 | 최근 120건 그리드 · 상태 필터(완료/부분/실패) · 프롬프트 검색 (URL 쿼리 유지) | `GET /jobs?limit=120` |
| `/jobs/:id` | 작업 상세 | 결과 · 해석 JSON 복사 · 메타 · 평가/정답 알려주기 · 같은 문장으로 다시 작업 | `GET /jobs/{id}`, `POST /feedback` |
| `/guide` | 프롬프트 가이드 | 남기기 vs 지우기 · 위치/크기/순서/개수/색 고르기 · 예시(누르면 작업실로) · 한계 | — |
| `/batch` | 배치 (Phase 2) | 여러 장 등록 · 상태 조회. **처리 워커는 미구현**이라 화면에 명시 | `POST /batch`, `GET /batch/{id}` |
| 그 외 | 404 | | |

상단 내비게이션 우측 점은 백엔드 상태(`GET /health`, 30초마다)다.

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
| 페이지 | `src/pages/` | Home · Studio · History · JobDetail · Guide · Batch · NotFound |
| 레이아웃 | `src/components/layout/AppLayout.tsx` | 내비게이션 · 서버 상태 · 푸터 |
| 이미지 | `src/components/image/` | 드롭존, Before/After, 진행 상태, `ResultImage`(투명 체크무늬) |
| 프롬프트 | `src/components/prompt/` | 입력, 예시 칩, `ParsedPromptView`(해석 칩) |
| 피드백 | `src/components/feedback/FeedbackPanel.tsx` | 좋아요/싫어요 + 정답 알려주기 |
| 작업 | `src/components/jobs/JobCard.tsx` | 썸네일 카드 |
| 공통 | `src/components/common/` | Button, PageHeader, StatusBadge, 로딩/에러/빈 상태 |
| 상태 | `src/store/useAppStore.ts` | 작업실 입력·결과 (페이지를 옮겨도 유지) |
| API | `src/api/client.ts` | axios → backend `/api/v1` (업로드 타임아웃 180s) |
| 훅 | `src/hooks/` | `useImageProcessing`, `useFeedback(jobId)`, `useApi`(jobs·job·health) |
| 데이터 | `src/data/examples.ts` | 홈·작업실·가이드 공용 예시 프롬프트 |
| 포맷 | `src/utils/formatters.ts` | 점수·크기·날짜(UTC→로컬)·효과/위치/클래스 한국어 라벨 |

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

## 관련 문서

- `docs/guidance/user-frontend.md` — 사용 흐름
- `docs/guidance/llm-and-vision.md` — 프롬프트 규격 (selector · remove_object)
- `docs/API_DOCUMENTATION.md`
- `docs/Architecture/apps.md`
- `RUN.md`
