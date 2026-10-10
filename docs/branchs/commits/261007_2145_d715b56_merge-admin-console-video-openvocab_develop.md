# 부족한 부분 보완 + 운영 콘솔(관리자) 작업 8개 브랜치 총 병합 / `d715b56`

> 브랜치: `develop`  
> 작성일: `2026-10-07 21:45`  
> 작성자: `agent`  
> 파일명: `261007_2145_d715b56_merge-admin-console-video-openvocab_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge(develop): 부족한 부분 보완 + 운영 콘솔 작업 8개 브랜치 총 병합` |
| **병합 커밋 (쌓인 순서)** | `9818826` cleanup-image-processor → `fde3c55` open-vocab-tune → `cc80786` video-webm → `af655b4` console-auth → `8da5f91` console-users → `f837092` console-system → `247e1eb` open-vocab-eval → `d715b56` ui-check-console |
| **브랜치** | `develop` (`git merge --no-ff`, 사용자 지시 "부족한 부분 → 관리자 페이지 → 모두 끝나면 커밋 후 최종 병합" 에 따라 마지막에 한 번) |
| **병합 전 develop** | `76cf3cf` |

## 2. 주 커밋 내용

| 브랜치 | 커밋 | 내용 |
|--------|------|------|
| `feature/cleanup-image-processor` | `3f19331` | selector 를 건너뛰던 죽은 코드 `ImageProcessor.run` 삭제 |
| `feature/open-vocab-tune` | `15e2eed` | DINO 전용 임계값(0.35/0.25)·빈 라벨 박스 제거·기동 워밍업 |
| `feature/video-webm` | `ec4c7d1` | 영상 결과 webm(VP8) — 페이지에서 바로 재생, 인코더 없으면 avi 폴백 |
| `feature/console-auth` | `afa4033` | 콘솔 관리자 로그인(`CONSOLE_ADMINS`), `CONSOLE_REQUIRE_LOGIN`, 검수자 기록 |
| `feature/console-users` | `940999b` | 회원 관리: 검색·잠금 해제·세션 끊기·계정 삭제(파일 포함) |
| `feature/console-system` | `1641779` | 시스템: 런타임·저장 공간·배포 점검, 보관 기간 정리(미리 보기 → 실행) |
| `feature/open-vocab-eval` | `82d1be2` | 임계값 측정(COCO 3,000쌍) + 헬멧 판정 정정 |
| `feature/ui-check-console` | `896eda3` | 실브라우저 17개 흐름 확인 (문제 0건) |

## 3. 상세 내용

### 3.1 배경 / 목적
직전 작업에서 남긴 부족한 부분(오픈 보캐브 오검출 판단·첫 요청 지연, 영상 재생 불가, 죽은 코드)을 메우고,
운영 콘솔의 보안 구멍(리버스 프록시 뒤 무인증 노출)과 부족한 관리 기능(회원·시스템)을 채웠다.

### 3.2 변경 범위
각 브랜치 커밋 기록 참조.

### 3.3 기술 포인트
- 충돌 없음. 중간 병합 없이 8개를 쌓인 순서대로 병합
- 콘솔 배포 시 `CONSOLE_REQUIRE_LOGIN=true` + `CONSOLE_ADMINS` 설정 필요 (preflight 경고)

### 3.4 의도적으로 하지 않은 것
- main 병합 · push · 배포, 광학 흐름/LSTM, 클라우드 LLM 스모크(키 없음)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 병합 후 백엔드 pytest 275 passed, 프론트 vitest 32 · build, 콘솔 vitest 21 · build 통과
- [x] 실브라우저 확인(병합 전 최상단 브랜치 = 병합 결과와 같은 트리) 17개 흐름 통과, 문제 0건

### 4.2 부작용 / 리스크
- `15e2eed` 커밋 본문의 "헬멧 없는 사진" 전제는 틀렸다 — `82d1be2` 문서에서 정정
- origin 에는 push 하지 않음

### 4.3 후속 작업
- push 지시 시 푸시, 배포(보류), s→m 캐스케이드 측정(사용자 답 대기)

### 4.4 관련 문서
- `docs/guidance/console-admin.md`, `docs/vaildates/open-vocab-20261007.md`, `docs/vaildates/ui-check-20261007-console.md`
