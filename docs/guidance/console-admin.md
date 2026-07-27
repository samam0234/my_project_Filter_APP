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

## 화면

| 메뉴 | 역할 |
|------|------|
| 대시보드 | API/DB 상태, Job 집계, 최근 5건 |
| Job 목록 | 전체 Job 테이블, after 미리보기 링크 |
| 시스템 | version, dialect, 포트 메모 |
| 바로가기 | frontend / swagger / health |

## 자동 갱신

30초 간격 + 수동 새로고침 버튼.

## 보안 주의

Phase 1은 **인증 없음**. 배포 시 reverse proxy 인증 또는 내부망 전용으로 제한할 것.
