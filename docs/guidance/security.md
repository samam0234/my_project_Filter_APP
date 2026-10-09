# 보안 · 운영 점검표

공개 배포 전에 이 표를 위에서부터 확인한다. "자동"은 코드가 이미 하고 있는 것, "수동"은 배포하는 사람이 정해야 하는 것.

배포 순서 전체는 [../DEPLOYMENT.md](../DEPLOYMENT.md). 아래 항목 대부분은 두 스크립트가 대신 확인한다:
- `python scripts/make_prod_env.py` — 1절 값을 채우고 새 비밀 값을 만든 뒤 preflight 까지 (`.env.production`)
- `python scripts/deploy_check.py remote https://도메인` · `server [--gpu]` — 2절 네트워크 · 헤더 · 인증서, 모델 · 백업 · Docker

## 1. 설정 (`.env`)

| 항목 | 배포 값 | 확인 방법 |
|------|---------|-----------|
| `APP_ENV` | `production` — 아래 위험한 기본값이 남아 있으면 **기동 거부** | `python -m app.core.preflight` (backend/) |
| `SECRET_KEY` | 32자 이상 난수 `python -c "import secrets; print(secrets.token_urlsafe(48))"` | preflight |
| `DEBUG` | `false` | preflight |
| `SESSION_COOKIE_SECURE` | `true` (HTTPS 일 때만 — http 에서 켜면 로그인이 안 된다) | preflight |
| `SMTP_*` | 실제 메일 서버 — 비우면 비밀번호 재설정 코드가 **서버 로그**에 남는다 | preflight |
| `MARIADB_PASSWORD` | 기본값(`cutnkeep`) 금지 | preflight |
| `CONSOLE_ADMINS` · `CONSOLE_REQUIRE_LOGIN=true` | 운영 콘솔은 관리자 로그인으로만 | [console-admin.md](./console-admin.md) |
| `CONSOLE_ALLOW_REMOTE` | `false` | — |

## 2. 네트워크

| 항목 | 상태 |
|------|------|
| 공개 포트 | **frontend :80 만** (nginx). backend :8000 · MariaDB · Redis · Adminer 는 `127.0.0.1` 에만 열린다 (`BIND_HOST`, 기본 127.0.0.1). 다른 기기에서 직접 열어야 할 때만 `BIND_HOST=0.0.0.0` |
| HTTPS | `docker-compose.https.yml` — Caddy 가 인증서 자동 발급·갱신, http→https, Secure 쿠키 · HSTS 자동 ([https-deploy.md](./https-deploy.md)). **수동**: 도메인 · DNS · 80/443 개방 |
| 보안 헤더 | 자동 — nginx: CSP(스크립트 같은 출처만) · `X-Frame-Options: DENY` · `nosniff` · `Referrer-Policy` · `Permissions-Policy`, `server_tokens off` |
| 비로그인 업로드 한도 | 자동 — 분당 `UPLOAD_RATE_GUEST_PER_MIN`. nginx 뒤에서도 사람(IP)마다 따로 세도록 `TRUSTED_PROXIES`(compose 기본 172.16.0.0/12)에서 온 `X-Real-IP` 를 쓴다. 콘솔의 "이 PC" 판정은 이 헤더를 믿지 않는다 |
| 로그인 | 자동 — 연속 실패 시 계정 잠금, 세션은 HttpOnly 쿠키 ([auth.md](./auth.md)) |

## 3. 업로드

| 공격 | 막는 곳 |
|------|---------|
| 확장자·MIME 위장 | 내용 시그니처 검사 (사진 JPEG·PNG·WebP · 영상 AVI·MP4·WebM · GIF) |
| 압축 폭탄 (파일은 작고 풀면 수 GB) | 디코딩 전에 해상도 확인 — 사진 `MAX_IMAGE_PIXELS`(40MP) · GIF 한 프레임 `GIF_MAX_PIXELS`(4MP) · 영상 긴 변 `VIDEO_MAX_SIDE`(3840) |
| 큰 파일 | 사진·GIF `MAX_UPLOAD_SIZE_MB`(20) · 영상 `VIDEO_MAX_UPLOAD_MB`(80) · nginx 25MB/85MB |
| 오래 걸리는 처리 | 영상·GIF 프레임 상한(`VIDEO_MAX_FRAMES` · `GIF_MAX_FRAMES`), nginx 대기 600초 |
| 남의 파일 보기 | 결과 파일은 작업 소유자만 (`/files/*` 404), 파일 경로는 업로드 폴더 안인지 확인 |

## 4. 데이터 보관 · 개인정보

| 항목 | 상태 |
|------|------|
| 업로드 파일 삭제 | **자동** — 백엔드가 `FILE_CLEANUP_MINUTES`(60)마다 `FILE_RETENTION_HOURS`(24)가 지난 파일을 지운다. 예전에는 `scripts/cleanup.py` 를 누가 돌려야 지워졌다 |
| 서비스 DB 백업 | **자동** — SQLite 면 기동 직후 + `DB_BACKUP_HOURS`(24)마다 `backend/data/backups/` 에 온라인 백업, 최근 `DB_BACKUP_KEEP`(7)개. 깨진 백업은 버린다 ([DATABASE.md](../plan/DATABASE.md)) |
| MariaDB 백업 (서비스 + 학습 DB) | **자동** — `mariadb-backup` 서비스, 24시간마다 · 7일 보관, 복구 절차·확인은 [DATABASE.md](../plan/DATABASE.md). **수동**: 백업 파일을 다른 디스크 · PC 로 복사 |
| 이용자 안내 | 회원가입 화면 · 프롬프트 가이드에 보관 기간(24시간)과 학습 이용(운영자 검수 후 문장만)을 안내 |
| 학습 후보 | 요청 문장 + 해석. 회원 삭제 시 계정 연결을 끊는다 |
| 실패 · 확신 낮은 요청의 원본 사진 (`data/feedback`) | **자동** — `FEEDBACK_IMAGE_RETENTION_DAYS`(30)일 뒤 삭제, 계정 삭제 시 바로 삭제 (`services/feedback_images.py`). 처리방침에 같은 일수 표시 |
| 어려운 사례 수집 `HARD_EXAMPLE_CONF` | 기본 꺼짐 — 켜면 실패하지 않은 요청 중 확신 낮은 것의 사진도 위 규칙으로 남는다 (처리방침은 이미 이 경우를 포함) |
| 개인정보 처리방침 · 이용약관 | 화면 `/privacy` · `/terms`, 가입 시 [필수] 만 14세 · 동의 체크(서버 검사 · 시각 기록). **수동**: 운영자 정보 `OPERATOR_*` 채우기 · 법률 검토 ([legal.md](./legal.md)) |

## 5. 의존성 취약점 점검

2026-10-10 에 처음 돌렸다:

| 대상 | 결과 | 조치 |
|------|------|------|
| Python (`requirements.docker.txt` · `requirements.txt`, `pip-audit`) | **9개 패키지에 알려진 취약점** — Pillow 10.4(33건) · python-multipart 0.0.9(14) · starlette 0.38(14, FastAPI 경유) · langchain-core 0.3(13) · cryptography 43(10) · langgraph-checkpoint(6) · langsmith(5) · langgraph 0.2(3) · python-dotenv(2) | 고친 판으로 올림: FastAPI 0.143 · starlette 1.7 · python-multipart 0.0.32 · Pillow 12.3 · cryptography 50.0 · langgraph 1.2 · langchain-core 1.6 · pydantic 2.14 등 → **0건**, 테스트 451 통과 · Docker 이미지 확인 |
| 프론트 · 콘솔 배포 의존성 (`npm audit --omit=dev`) | 0건 | — |
| 프론트 · 콘솔 개발 도구 (`npm audit`) | 7건 (moderate 2 · high 5) — 빌드 도구의 `postcss-selector-parser` | 브라우저로 나가는 코드가 아니다. 고치려면 `npm audit fix --force`(깨질 수 있는 업그레이드)라 보류 |

다시 돌리기:

```bash
pip install pip-audit && PYTHONUTF8=1 pip-audit -r requirements.docker.txt    # Windows 는 PYTHONUTF8=1 (한글 주석)
cd frontend && npm audit --omit=dev && cd ../console && npm audit --omit=dev
```

## 6. 아직 안 한 것

- 침투 테스트 (pip-audit 은 CI 에 넣었다 — push 마다 · 매주 월요일. npm 개발 도구 7건은 보류)
- 여러 서버로 늘릴 때 속도 제한을 Redis 로 (지금은 프로세스 메모리)
