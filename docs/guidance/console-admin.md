# Ops Console 가이드

## 위치

- 코드: 저장소 루트 `console/`
- 기술: React + TypeScript + Vite + Tailwind + Zustand
- 포트: **5174**

## 실행

```bash
cd console
npm install
npm run dev
```

Backend(`8000`)가 떠 있어야 Job/헬스 데이터가 채워진다.
콘솔은 **백엔드와 같은 PC** 에서 실행한다 — 전체 작업 조회 API(`/api/v1/console/*`)가 loopback 요청만 허용하기 때문이다.

## 화면

| 메뉴 | 역할 |
|------|------|
| 대시보드 | API/DB 상태, Job 집계, 최근 5건 |
| Job 목록 | 전체 Job 테이블 (회원 작업 + 로그인 기능 이전의 소유자 없는 작업), after 미리보기 링크 |
| 시스템 | version, dialect, 포트 메모 |
| 바로가기 | frontend / swagger / health |

## 자동 갱신

30초 간격 + 수동 새로고침 버튼.

## API

| 콘솔 호출 | 백엔드 |
|-----------|--------|
| 헬스 | `GET /health` |
| Job 목록 · 단건 | `GET /api/v1/console/jobs` · `/console/jobs/{id}` |
| after 링크 | `GET /api/v1/console/files/{id}/after` |

사용자 앱의 `/api/v1/jobs` 는 로그인 사용자 **본인 작업만** 돌려주므로 콘솔은 쓰지 않는다.

## 보안 주의

콘솔 자체는 **로그인이 없다**. 대신 콘솔 API 는 서버 PC(loopback) 요청만 받는다.
원격에서 써야 하면 reverse proxy 인증·VPN 등 앞단 접근 제어를 한 뒤 `CONSOLE_ALLOW_REMOTE=true`.
