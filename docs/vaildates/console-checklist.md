# Console Validation

| 항목 | 기대 |
|------|------|
| 기동 | http://localhost:5174 로드 (백엔드와 같은 PC) |
| API offline | 경고 배너 표시 |
| API online | 사이드바 online, dialect 표시 |
| Job 목록 | 업로드(로그인 회원) 후 새로고침 시 행 증가 · 소유자 없는 옛 작업도 표시 |
| after 링크 | `/api/v1/console/files/{id}/after` 열림 |
| 원격 접근 | 다른 PC 에서 콘솔 API 호출 시 403 (`CONSOLE_ALLOW_REMOTE=false`) |
| 30s auto refresh | 네트워크 탭 주기 호출 |
