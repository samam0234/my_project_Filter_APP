# Applications

## frontend/ (User App)

- React + TS + Vite + Tailwind + Zustand · 자체 최소 라우터(`src/router.tsx`, History API)
- 페이지: 홈 `/`(원본/결과 데모) · 작업실 `/studio`(**사진 · GIF 탭**) · 작업 기록 `/history`(사진 · 영상 · GIF) · 작업 상세 `/jobs/:id` · 프롬프트 가이드 `/guide` · 배치 `/batch` · 영상 `/video` · 계정 화면
- 작업실: 단계(업로드 · 문장 · 처리) · 처리 진행 · 해석 칩 · Before/After · 평가 + **정답 알려주기**(LoRA 학습 정답)
- 디자인: 다크 테마 · Pretendard · 공통 클래스(`card` · `field` · `buttonClass`) · 1024px 미만 펼침 메뉴
- 계정: 로그인 · 회원가입 · 아이디/비밀번호 찾기. **비로그인은 처리·다운로드만**, 작업 기록·상세·피드백·배치는 회원 전용
- Port **5173** · 상세 `frontend/README.md`

## console/ (Ops Admin)

- React + TS + Vite + Tailwind + Zustand
- 대시보드 · 작업 목록 · 학습 데이터 검수 · 배치 현황 · 회원 관리 · 시스템(설정 점검 · 저장 공간 · 정리)
- Port **5174**
- 콘솔 API(`/api/v1/console/*`)는 **관리자 로그인**(`CONSOLE_ADMINS`) 또는 서버 PC(`CONSOLE_REQUIRE_LOGIN=false`) — `docs/guidance/console-admin.md`

## backend/

- FastAPI, SQLAlchemy, OpenCV pipeline
- Port **8000**
