# Pre-deploy Checklist

- [ ] `.env` 시크릿 교체 (`SECRET_KEY`, DB password)
- [ ] 계정 메일: `SMTP_HOST`·`SMTP_USER`·`SMTP_PASSWORD`·`SMTP_FROM` 설정 (미설정이면 인증 코드가 서버 로그에 남음)
- [ ] HTTPS 뒤에서 `SESSION_COOKIE_SECURE=true`, `CORS_ORIGINS` 에 실제 도메인
- [ ] 로그 접근 권한 제한 (`backend/logs`)
- [ ] `DB_DIALECT=mariadb` 및 호스트 확인
- [ ] 이미지 빌드 성공 (`backend`, `frontend`)
- [ ] 포트 충돌 없음 (`ports-inventory.md`)
- [ ] 콘솔 외부 노출 여부 결정 (기본 비권장/내부망). 콘솔 API 는 기본 loopback 전용 — 원격은 앞단 인증 후 `CONSOLE_ALLOW_REMOTE=true`
- [ ] 백업: MariaDB 볼륨 / 피드백 데이터
