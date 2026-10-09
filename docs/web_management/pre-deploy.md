# Pre-deploy Checklist

> 설정 · 네트워크 · 업로드 방어 · 자동 정리 · 백업 · 개인정보를 한 장에 모은 점검표: [`docs/guidance/security.md`](../guidance/security.md)

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
      reverse proxy 뒤면 `TRUSTED_PROXIES=<프록시 대역>` (Docker compose 는 172.16.0.0/12 기본) — 안 하면 모든 비로그인 사용자가 프록시 IP 하나로 묶인다
- [ ] uvicorn 워커 1개 기준 (속도 제한·모델이 프로세스 메모리) — 늘리려면 속도 제한을 Redis 로
- [x] 업로드 파일 정리 — 백엔드가 `FILE_CLEANUP_MINUTES`(60)마다 자동 (`FILE_RETENTION_HOURS` 24). 별도 cron 불필요 (끄려면 0)
- [ ] CI 통과 (`.github/workflows/ci.yml`)
- [ ] 프론트 개발 도구 취약점: 배포 번들은 0건. `npm audit`(dev 포함) 은 2026-10-06 vite 7 · vitest 5 로 올려 10건(치명 2) → 7건(높음 5 · 중간 2)
      — 남은 건 전부 **tailwindcss 3** 계열(braces·chokidar·postcss-selector-parser, 빌드 시점) → tailwind 4 마이그레이션 별도 작업.
      dev 서버(`npm run dev`)를 외부망에 열지 말 것
- [ ] 이미지 빌드 성공 (`backend`, `frontend`)
- [ ] 포트 충돌 없음 (`ports-inventory.md`)
- [ ] 콘솔 외부 노출 여부 결정 (기본 비권장/내부망). 원격은 `CONSOLE_ADMINS` 관리자 로그인 + `CONSOLE_REQUIRE_LOGIN=true` ([console-admin.md](../guidance/console-admin.md))
- [x] 서비스 DB(SQLite) 백업 — 자동 (`DB_BACKUP_HOURS` 24, 최근 7개, `backend/data/backups/`)
- [ ] 백업: MariaDB(학습 DB) `mysqldump` 정기 실행 / 피드백 데이터(`data/feedback`)
- [ ] 내부 포트 127.0.0.1 바인딩 확인 (`docker ps` 의 PORTS 가 `127.0.0.1:` 로 시작) — 공개는 :80
- [ ] 대상 지우기 LaMa 모델 배치 (`backend/models/lama_fp32.onnx`) — 없으면 Telea
- [ ] 개인정보 처리방침 · 이용약관 — `.env` 의 `OPERATOR_NAME` · `OPERATOR_EMAIL` · `POLICY_DATE` 채우고 frontend 다시 빌드, 법률 검토 ([legal.md](../guidance/legal.md))
- [ ] HTTPS — `docker-compose.https.yml` + `DOMAIN` · `ACME_EMAIL` ([https-deploy.md](../guidance/https-deploy.md))
- [ ] 메일 — `python scripts/send_test_mail.py 내주소` 로 발송 확인
