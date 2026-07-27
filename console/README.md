# Cut & Keep · Ops Console

운영·모니터링용 **관리자 React 앱** (`console/`).

## 실행

```bash
cd console
npm install
npm run dev
```

- URL: http://localhost:5174  
- Backend API: http://localhost:8000 (Vite proxy)

## 기능

| 메뉴 | 설명 |
|------|------|
| 대시보드 | 헬스, Job 집계, 최근 목록 |
| Job 목록 | `GET /api/v1/jobs` 테이블 |
| 시스템 | dialect, version, 포트 정보 |
| 바로가기 | 사용자 앱 / Swagger / Health |

## 사용자 앱과의 차이

| | `frontend/` | `console/` |
|--|-------------|------------|
| 대상 | 일반 사용자 | 운영자 |
| 포트 | 5173 | 5174 |
| 핵심 | 업로드·필터 | Job/헬스 모니터링 |

가이드: `docs/guidance/console-admin.md`
