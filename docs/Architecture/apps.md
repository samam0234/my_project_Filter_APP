# Applications

## frontend/ (User App)

- React + TS + Vite + Tailwind + Zustand · 자체 최소 라우터(`src/router.tsx`, History API)
- 페이지 6개: 홈 `/` · 작업실 `/studio` · 작업 기록 `/history` · 작업 상세 `/jobs/:id` · 프롬프트 가이드 `/guide` · 배치 `/batch`
- 작업실: 업로드 · 프롬프트 · 처리 진행 · 해석 칩 · Before/After · 평가 + **정답 알려주기**(LoRA 학습 정답)
- 계정: 로그인 · 회원가입 · 아이디/비밀번호 찾기. **비로그인은 처리·다운로드만**, 작업 기록·상세·피드백·배치는 회원 전용
- Port **5173** · 상세 `frontend/README.md`

## console/ (Ops Admin)

- React + TS + Vite + Tailwind + Zustand
- Job 목록, 헬스, 집계 대시보드
- Port **5174**
- 콘솔 로그인 없음 — 대신 콘솔 API(`/api/v1/console/*`)는 **서버 PC(loopback)만** 허용. 원격 사용 시 앞단 인증 후 `CONSOLE_ALLOW_REMOTE=true`

## backend/

- FastAPI, SQLAlchemy, OpenCV pipeline
- Port **8000**
