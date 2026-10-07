# 결과를 브라우저에 보관해 다시 재생·저장하고, 문장을 고쳐 다시 처리할 수 있게 / `920362da580eae8fbf6f1f21b974e72442a582c1`

> 브랜치: `feature/video-fixes`  
> 작성일: `2026-10-07 22:57`  
> 작성자: `agent`  
> 파일명: `261007_2257_920362d_video-browser-storage-retry_feature-video-fixes.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(video): 결과를 브라우저에 보관해 다시 재생·저장하고, 문장을 고쳐 다시 처리할 수 있게` |
| **커밋 번호 (SHA)** | `920362da580eae8fbf6f1f21b974e72442a582c1` |
| **짧은 SHA** | `920362d` |
| **브랜치** | `feature/video-fixes` |
| **부모 커밋** | `8ae8528` |

## 2. 주 커밋 내용

- `frontend/src/utils/videoStore.ts`: 마지막 결과 1건을 **IndexedDB** 에 보관·복원·삭제 (계정별 분리, 실패 시 예외 대신 null/false)
- 영상 페이지: 새로고침해도 보관된 결과 재생·저장, "다시 처리" 버튼, 해석된 효과·강도 표시, 재생 실패 안내, 보관 지우기
- `VideoFormat` 에 mp4, 클라이언트가 효과·강도·형식 헤더를 읽음 (헤더가 없으면 Content-Type 으로 판별)
- `ui_check.py`: mp4 받기·새로고침 후 되살리기·다시 처리·**1080p 영상의 받은 파일 선명도 비교** 추가
- 문서: API · 사용자 가이드 · 브라우저 확인 결과

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지적 ② "처리 후 재생을 못한다 → 처리 후 재생은 로컬 스토리지로", ③ "블러가 안 된 파일이 나오면 다시 작업할 수 있게".

### 3.2 변경 범위
- 추가: `frontend/src/utils/videoStore.ts`, `videoStore.test.ts`, devDependency `fake-indexeddb`
- 수정: `frontend/src/pages/{VideoPage,VideoPage.test}.tsx`, `frontend/src/api/{client,client.test}.ts`, `frontend/src/types/index.ts`,
  `scripts/experiments/ui_check.py`, `docs/API_DOCUMENTATION.md`, `docs/guidance/user-frontend.md`, `docs/vaildates/ui-check-20261007-console.md`

### 3.3 기술 포인트
- "로컬 스토리지"는 **IndexedDB** 로 구현 — localStorage 는 문자열만·약 5MB 라 영상을 담을 수 없다 (같은 브라우저 로컬 저장소)
- 마지막 1건만 보관 → 용량 무한 증가·개인 영상 누적 방지. `owner`(`guest` 또는 회원 id)가 다르면 되살리지 않음
- 비로그인은 서버에 아무것도 안 남으므로 이 보관이 유일한 "다시 보기"
- 보관에서 되살린 결과는 원본이 없어 다시 처리하려면 영상을 다시 올려야 함 (화면에 안내)
- 보관 Blob 은 Blob 객체로 저장 (base64 변환 없음)

### 3.4 의도적으로 하지 않은 것
- 보관 개수 확장(여러 건 목록), 서버 보관 기간 연장

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 프론트 vitest 44 · tsc · build 통과
- [x] 실브라우저(Chromium) 18개 흐름, 문제 0건 — 비로그인 영상: 재생 → mp4 받기 → **새로고침 → 보관본 되살아나 재생** → 원본 다시 올려 다시 처리
- [x] 1080p+: 받은 mp4(1920×1440, H.264 yuv420p)를 OpenCV 로 열어 원본 대비 선명도 0.126 — 화면 캡처로 사람은 선명, 배경은 흐림 확인

### 4.2 부작용 / 리스크
- jsdom 은 Blob 복제 구현이 달라 보관소 단위 테스트에서 Blob 크기는 검증하지 못함 → 실제 Chromium 새로고침 흐름으로 보완
- 브라우저 저장소를 못 쓰는 환경(시크릿 창 등)은 새로고침하면 결과가 사라짐 — 화면에 안내

### 4.3 후속 작업
- 사용자 확인 후 병합 (아직 병합하지 않음)

### 4.4 관련 문서
- `docs/guidance/user-frontend.md`, `docs/vaildates/ui-check-20261007-console.md`
