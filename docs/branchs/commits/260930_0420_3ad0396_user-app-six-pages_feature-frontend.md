# 사용자 앱 6개 페이지와 정답 알려주기 추가 / `3ad03967f4047328cadc95d056a2df94adc3ab77`

> 브랜치: `feature/frontend`  
> 작성일: `2026-09-30 04:20`  
> 작성자: `agent`  
> 파일명: `260930_0420_3ad0396_user-app-six-pages_feature-frontend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(frontend): 사용자 앱 6개 페이지와 정답 알려주기 추가` |
| **커밋 번호 (SHA)** | `3ad03967f4047328cadc95d056a2df94adc3ab77` |
| **짧은 SHA** | `3ad0396` |
| **브랜치** | `feature/frontend` |
| **부모 커밋** | `212b765` |

## 2. 주 커밋 내용

- 페이지 6개: 홈 · 작업실 · 작업 기록 · 작업 상세 · 프롬프트 가이드 · 배치 (+ 404)
- 자체 최소 라우터 `src/router.tsx` (History API, 새 의존성 없음)
- 정답 알려주기: 해석을 미리 채운 교정 폼 → ParsedPrompt JSON 을 dislike 코멘트로 전송
- 해석 칩(`ParsedPromptView`), 처리 경과 시간/단계, 결과 저장, 백엔드 상태 표시
- 투명 체크무늬 미생성 버그, 좁은 화면 그리드 폭 수정

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 앱은 업로드·프롬프트·결과가 한 화면에 있는 Phase 1 스켈레톤이었다.
인스턴스 선택·물체 지우기가 들어오면서 사용자가 **서버가 문장을 어떻게 이해했는지** 보고,
틀렸을 때 **정답을 알려 줄** 길이 필요했다 (LoRA 재학습 데이터).
지난 작업을 다시 보는 화면과 쓰는 법 안내도 없었다.

### 3.2 변경 범위

- 추가된 경로:
  - `src/router.tsx`, `src/pages/*` (7개), `src/components/layout/AppLayout.tsx`
  - `src/components/common/{PageHeader,States,StatusBadge}.tsx`
  - `src/components/feedback/FeedbackPanel.tsx`, `src/components/jobs/JobCard.tsx`
  - `src/components/image/ResultImage.tsx`, `src/components/prompt/{ExamplePrompts,ParsedPromptView}.tsx`
  - `src/hooks/useApi.ts`, `src/data/examples.ts`
- 수정된 경로: `App.tsx`, `api/client.ts`, `types/index.ts`, `utils/formatters.ts`, `hooks/useFeedback.ts`,
  `components/image/{BeforeAfterViewer,ProcessingStatus}.tsx`, `components/prompt/PromptInput.tsx`,
  `store/useAppStore.ts`, `index.css`
- 삭제된 경로: `components/feedback/FeedbackButtons.tsx` (→ FeedbackPanel), `components/batch/BatchUploader.tsx` (→ BatchPage)

### 3.3 기술 포인트

- 라우터: `useSyncExternalStore` 로 pathname 구독, `Link` 는 수정키·새 탭 클릭 시 기본 동작 유지.
  nginx `try_files` 와 Vite dev 서버가 직접 접근·새로고침을 처리
- 작업 기록 필터는 URL 쿼리(`?status=&q=`)에 `replace` 로 저장
- `created_at` 이 UTC(시간대 표기 없음)라 `Z` 를 붙여 로컬 시간으로 표시
- `useAsync` 는 요청 순번으로 늦게 도착한 응답·언마운트 뒤 응답을 무시
- 체크무늬: 기존 `bg-[url('data:image/svg+xml;… <svg xmlns…')]` 는 공백 때문에 Tailwind 가 클래스로
  생성하지 못했다(빌드 CSS 에 없음). `index.css` `.bg-checker`(linear-gradient)로 교체
- 교정 폼 출력은 `prompt_spec.parsed_to_json` 과 같은 키 → `training/lora/dataset.comment_as_parsed` 로 정답 인식 확인

### 3.4 의도적으로 하지 않은 것

- react-router 등 라우팅 라이브러리 추가
- 배치 처리 (백엔드 워커가 Phase 2 하드코딩 구간)
- 작업 삭제, 로그인

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `npm run build` (tsc -b + vite) 통과
- [x] headless Chrome 스크린샷으로 6개 페이지 + 404 + 390px 폭 확인
- [x] Vite 프록시 경유 업로드 ("사람 2명만 남기고 배경 블러" → count 2, 9.8 s)
- [x] 교정 JSON 이 LoRA 데이터 로더에서 정답으로 파싱됨 (오프라인 검증, 실제 피드백은 저장하지 않음)
- [ ] 브라우저 수동 클릭 테스트 (정답 보내기 → 서버 저장)

### 4.2 부작용 / 리스크

- 작업실 상태는 메모리(Zustand) — 새로고침하면 초기화
- 결과 파일은 서버 보관 시간 뒤 지워져 오래된 작업 카드는 "이미지 없음"
- 이전 curl 테스트로 한글이 깨진 채 저장된 작업 몇 건이 기록 화면에 그대로 보임 (데이터 문제)

### 4.3 후속 작업

- 배치 워커 구현 후 BatchPage 진행률 폴링
- develop 병합

### 4.4 관련 문서

- `frontend/README.md`, `docs/guidance/user-frontend.md`
