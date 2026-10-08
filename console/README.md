# Cut & Keep · Ops Console

운영·모니터링용 **관리자 React 앱** (`console/`).

## 실행

**필수:** 최초 1회(또는 `node_modules` 없을 때) `npm install`  
`node_modules` 없이 `npm run dev` 하면 `vite` 를 찾지 못해 실패한다.

```bash
cd console
npm install
npm run dev
```

- URL: http://localhost:5174  
- Backend API: http://localhost:8000 (Vite proxy)  
- API 데이터(Job/헬스)는 **backend :8000** 이 떠 있어야 채워진다. UI 자체는 backend 없이도 기동된다.
- 콘솔 API(`/api/v1/console/*`)는 **관리자 로그인**(`CONSOLE_ADMINS`) 또는 **서버 PC**(`CONSOLE_REQUIRE_LOGIN=false` 일 때) — [`docs/guidance/console-admin.md`](../docs/guidance/console-admin.md)

## 기능

| 메뉴 | 설명 |
|------|------|
| 대시보드 | 헬스, Job 집계, 최근 목록 |
| Job 목록 | `GET /api/v1/console/jobs` 테이블 (전체 작업 — 사진 · 영상 · GIF 표시) |
| 학습 데이터 | 좋아요 · 정답 알려주기 · 회원 요청 문장 검수 (승인 · 정답 고쳐서 승인 · 삭제) → RAG · LoRA |
| 배치 현황 | 전체 회원 배치 (이미지는 보이지 않음) |
| 회원 | 검색 · 잠금 해제 · 세션 끊기 · 계정 삭제(파일 포함) |
| 시스템 | 배포 설정 점검 · 세그/LLM/체인/마스크 처리(지우기 엔진 LaMa·Telea) · 저장 공간 · 정리 미리 보기/실행 |
| 바로가기 | 사용자 앱 / Swagger / Health |

## 사용자 앱과의 차이

| | `frontend/` | `console/` |
|--|-------------|------------|
| 대상 | 일반 사용자 | 운영자 |
| 포트 | 5173 | 5174 |
| 핵심 | 업로드·필터 | Job/헬스 모니터링 |

가이드: `docs/guidance/console-admin.md`
