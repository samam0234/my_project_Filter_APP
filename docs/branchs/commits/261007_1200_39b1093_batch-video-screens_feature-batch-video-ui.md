# 배치 결과 화면과 영상 페이지, 콘솔 배치 현황 / `39b1093d8c26f8fdb0f36a25fae42c4b95579f00`

> 브랜치: `feature/batch-video-ui`  
> 작성일: `2026-10-07 12:10`  
> 작성자: `agent`  
> 파일명: `261007_1200_39b1093_batch-video-screens_feature-batch-video-ui.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(frontend): 배치 결과 화면과 영상 페이지, 콘솔 배치 현황` |
| **커밋 번호 (SHA)** | `39b1093d8c26f8fdb0f36a25fae42c4b95579f00` |
| **짧은 SHA** | `39b1093` |
| **브랜치** | `feature/batch-video-ui` |
| **부모 커밋** | `770df3b` |

## 2. 주 커밋 내용

- 사용자 프론트: 배치 페이지 재작성(진행률 폴링, 항목별 전/후 이미지, zip 다운로드, 내 배치 목록)
- 사용자 프론트: 영상 페이지 신설(`/video`, 내비 "영상"), 처리 프레임 수·유지 프레임 수 표시
- 운영 콘솔: "배치 현황" 페이지(전체 사용자 배치 상태·진행률, 이미지 URL 없음)
- API 클라이언트·타입 확장, 결과 이미지 로드 실패 placeholder, 홈·가이드 문구에서 "준비 중" 제거
- 테스트: 프론트 30개, 콘솔 8개 통과

## 3. 상세 내용

### 3.1 배경 / 목적
인수인계(Grok) "배치·영상은 API만 있고 화면이 없다"를 해소. 앞선 `feature/batch-api` 커밋이 결과 서빙 API 를 마련해 화면을 붙일 수 있게 되었다.

### 3.2 변경 범위
- 추가: `frontend/src/pages/VideoPage.tsx`, `VideoPage.test.tsx`, `BatchPage.test.tsx`, `api/client.test.ts`, `console/src/pages/BatchesPage.tsx`, `BatchesPage.test.tsx`
- 수정: `frontend/src/{pages/BatchPage.tsx, App.tsx, components/layout/AppLayout.tsx, components/image/ResultImage.tsx, api/client.ts, types/index.ts}`, `console/src/{api/client.ts, types, Sidebar, App}`, 사용자·콘솔 가이드 문서, `scripts/experiments/ui_check.py`

### 3.3 기술 포인트
- `useBatchPolling(jobId, intervalMs=2000)` 로 완료·실패까지 폴링 후 정지
- 영상은 Blob 응답 → 오류 시 `unwrapBlobError`/`blobText` 로 서버 메시지 추출 (jsdom 은 Blob.text 없음 → FileReader 폴백)
- 콘솔 배치 현황은 개인정보(이미지)를 노출하지 않는 필드만 사용

### 3.4 의도적으로 하지 않은 것
- 영상 브라우저 재생용 재인코딩(현재 MJPG avi 는 다운로드 전용)
- 배포(Vercel/Cloudflare)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 프론트 vitest 30 · 콘솔 vitest 8 통과, 빌드 통과
- [x] Playwright 실브라우저 점검(`scripts/experiments/ui_check.py`) 13개 흐름 — 결과: `docs/vaildates/ui-check-20261007.md`

### 4.2 부작용 / 리스크
- 실브라우저 점검에서 `.avi` 업로드 거절 발견 → 다음 커밋 `f04c1a8` 에서 수정

### 4.3 후속 작업
- `f04c1a8` (영상 MIME 수정)

### 4.4 관련 문서
- `docs/guidance/user-frontend.md`, `docs/guidance/console-admin.md`, `docs/vaildates/ui-check-20261007.md`
