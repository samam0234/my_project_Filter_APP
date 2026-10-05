# Pre-deploy Checklist

**먼저 자동 점검**: `cd backend && APP_ENV=production python -m app.core.preflight` — 아래 항목 대부분을 검사한다.
`APP_ENV=production` 이면 서버도 기동 시 같은 점검을 하고, error 가 있으면 **뜨지 않는다** (`PREFLIGHT_STRICT=false` 로 경고만).

| 자동 점검 (error = 기동 거부) | 기준 |
|------------------------------|------|
| `SECRET_KEY` | 기본값이 아니고 32자 이상 |
| `DEBUG` | false |
| `SESSION_COOKIE_SECURE` | true (HTTPS) |
| `SMTP_HOST` | 설정 (없으면 재설정 코드가 로그에 남음) |
| `CORS_ORIGINS` | `*` 금지 (localhost 만이면 경고) |
| `MARIADB_PASSWORD` | 기본값 금지 (MariaDB 사용 시) |
| `OPENAI_API_KEY` · `GEMINI_API_KEY` | 해당 provider 일 때 필수 |
| `YOLO_MODEL_PATH` | 파일 존재 |
| 경고 | `CONSOLE_ALLOW_REMOTE=true`, `LEARNING_DB_FALLBACK_SQLITE=true` |


- [ ] `.env` 시크릿 교체 (`SECRET_KEY`, DB password)
- [ ] 계정 메일: `SMTP_HOST`·`SMTP_USER`·`SMTP_PASSWORD`·`SMTP_FROM` 설정 (미설정이면 인증 코드가 서버 로그에 남음)
- [ ] HTTPS 뒤에서 `SESSION_COOKIE_SECURE=true`, `CORS_ORIGINS` 에 실제 도메인
- [ ] 로그 접근 권한 제한 (`backend/logs`)
- [ ] 서비스 DB `DB_DIALECT=sqlite` (볼륨 백업) · 학습 DB `LEARNING_DB_DIALECT=mariadb` 호스트 확인, `/health` 의 `learning_db` 가 `mysql`
- [ ] 업로드 속도 제한 `UPLOAD_RATE_GUEST_PER_MIN`(6) · `UPLOAD_RATE_MEMBER_PER_MIN`(20) 검토.
      reverse proxy 뒤면 `uvicorn --proxy-headers --forwarded-allow-ips=<프록시 IP>` (안 하면 모든 사용자가 프록시 IP 하나로 묶임)
- [ ] uvicorn 워커 1개 기준 (속도 제한·모델이 프로세스 메모리) — 늘리려면 속도 제한을 Redis 로
- [ ] 업로드 파일 정리 `scripts/cleanup.py` 를 cron/작업 스케줄러에 등록 (`FILE_RETENTION_HOURS`)
- [ ] CI 통과 (`.github/workflows/ci.yml`)
- [ ] 프론트 개발 도구 취약점: 배포 번들은 0건, `npm audit`(dev 포함) 은 vite 5·esbuild·eslint 계열 10건 →
      vite 메이저 업그레이드 별도 작업. dev 서버(`npm run dev`)를 외부망에 열지 말 것
- [ ] 이미지 빌드 성공 (`backend`, `frontend`)
- [ ] 포트 충돌 없음 (`ports-inventory.md`)
- [ ] 콘솔 외부 노출 여부 결정 (기본 비권장/내부망). 콘솔 API 는 기본 loopback 전용 — 원격은 앞단 인증 후 `CONSOLE_ALLOW_REMOTE=true`
- [ ] 백업: MariaDB 볼륨 / 피드백 데이터
