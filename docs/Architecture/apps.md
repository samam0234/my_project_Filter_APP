# Applications

## frontend/ (User App)

- React + TS + Vite + Tailwind + Zustand · 자체 최소 라우터(`src/router.tsx`, History API)
- 페이지 6개: 홈 `/` · 작업실 `/studio` · 작업 기록 `/history` · 작업 상세 `/jobs/:id` · 프롬프트 가이드 `/guide` · 배치 `/batch`
- 작업실: 업로드 · 프롬프트 · 처리 진행 · 해석 칩 · Before/After · 평가 + **정답 알려주기**(LoRA 학습 정답)
- Port **5173** · 상세 `frontend/README.md`

## console/ (Ops Admin)

- React + TS + Vite + Tailwind + Zustand
- Job 목록, 헬스, 집계 대시보드
- Port **5174**
- **인증/권한은 Phase 1 미적용** (로컬 운영 전제) — 배포 시 보호 필요

## backend/

- FastAPI, SQLAlchemy, OpenCV pipeline
- Port **8000**
