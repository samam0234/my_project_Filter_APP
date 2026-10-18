# docker — Compose 스택과 보조 자산

> 컷앤킵 전체를 컨테이너로 띄우는 방법. 로컬 개발부터 HTTPS 공개 서버까지 같은 Compose 파일을 겹쳐 쓴다.

스택은 저장소 루트의 `docker-compose*.yml`이 정의하고, 이 폴더에는 그 스택이 쓰는 설정 파일(MariaDB · Caddy · nginx · 백업 스크립트)이 있다.

| 항목 | 값 |
|------|-----|
| 프로젝트 이름 | **`cut_and_keep`** (`-p cut_and_keep`) — 구 프로젝트명 `cutnkeep` 스택과 동시에 띄우지 않는다 |
| 네트워크 | `cut_and_keep_net` (bridge) |
| 환경 파일 | 루트 `.env` (`--env-file .env`) |
| 현재 구성 스냅샷 | [`docs/plan/CURRENT_STACK.md`](../docs/plan/CURRENT_STACK.md) |

---

## 1. Compose 파일

기본 파일 하나에 목적별 오버레이를 겹친다.

| 파일 | 용도 | 겹치는 방법 |
|------|------|-------------|
| `docker-compose.yml` | **기본 스택** — backend · frontend · MariaDB · Redis · Adminer · 백업 | 단독 |
| `docker-compose.https.yml` | **HTTPS 공개** — Caddy가 80 · 443을 받고 인증서 자동 발급 · 갱신, frontend는 밖으로 포트를 열지 않음, 세션 쿠키 Secure + HSTS | `-f docker-compose.yml -f docker-compose.https.yml` |
| `docker-compose.pc-ollama.yml` | **서버가 운영자 PC의 Ollama 쓰기** — `ollama-bridge`가 SSH 역방향 터널 끝으로 넘김 | 운영 서버에서 HTTPS와 함께 |
| `docker-compose.gpu.yml` | **NVIDIA GPU 서버** — CUDA torch + LoRA 이미지(`cut_and_keep-backend-gpu`), 해석 기본을 LoRA로 | HTTPS와 함께 써도 된다 |

```bash
# 로컬 개발
docker compose -p cut_and_keep --env-file .env up -d --build

# 운영 서버 (지금 공개 운영 구성)
DC='docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.pc-ollama.yml'
$DC up -d --build backend frontend caddy ollama-bridge     # 서비스를 지정한다 — 전체 up 은 Adminer 까지 띄운다

# GPU 서버
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.gpu.yml up -d --build
```

---

## 2. 서비스

| 서비스 | 이미지 / 빌드 | 호스트 포트 | 기본 `up` | 설명 |
|--------|---------------|-------------|-----------|------|
| `backend` | `backend/Dockerfile` (context = 루트) | `127.0.0.1:8000` (`BACKEND_PORT`) | ✅ | FastAPI. MariaDB가 healthy일 때만 뜬다 |
| `frontend` | `frontend/Dockerfile` | `80` | ✅ | nginx — 정적 화면 + `/api` · `/health` 프록시 · 보안 헤더 |
| `mariadb` | `mariadb:11` | `127.0.0.1:${MARIADB_PORT}` → 3306 | ✅ | 서비스 DB · 학습 DB. 비밀번호 인증만 |
| `redis` | `redis:7-alpine` | `127.0.0.1:6380` → 6379 | ✅ | 속도 제한 · (선택) 배치 큐 |
| `adminer` | `adminer:4` | `127.0.0.1:8081` | ✅ | DB 웹 관리 — **개발용**, 운영 서버에서는 띄우지 않는다 |
| `mariadb-backup` | `mariadb:11` + `mariadb/backup/backup.sh` | — | ✅ | `MARIADB_BACKUP_HOURS`(24)마다 덤프, `MARIADB_BACKUP_KEEP_DAYS`(7)일 보관 → `data/mariaDB_backups/` |
| `celery_worker` | `backend/Dockerfile` | — | ❌ 프로필 `phase2` | 배치를 Redis 워커로 처리할 때만 (`BATCH_USE_CELERY=true`) |
| `mailpit` | `axllent/mailpit:v1.20` | `127.0.0.1:8025` | ❌ 프로필 `mail` | 개발용 메일 받은편지함 — 밖으로 보내지 않고 웹에서 본다 |
| `caddy` | `caddy:2.8-alpine` | `80` · `443` | `https.yml` | HTTPS · 인증서 · `EDGE_SECRET` 검사 |
| `ollama-bridge` | `alpine/socat` (host 네트워크) | docker 게이트웨이 `172.18.0.1:11434` | `pc-ollama.yml` | 터널 끝 `127.0.0.1:11435`로 넘김 |

**공개 포트는 80(과 HTTPS에서 443) 하나다.** backend · MariaDB · Redis · Adminer · Mailpit은 `BIND_HOST`(기본 `127.0.0.1`)에만 열린다. 다른 기기에서 열어야 할 때만 `BIND_HOST=0.0.0.0`.

### 볼륨 (bind mount)

| 호스트 | 컨테이너 | 내용 |
|--------|----------|------|
| `./backend/data` | backend `/app/data` | 업로드 · (SQLite 모드일 때) 서비스 DB · 승인 문장 Chroma |
| `./backend/models` | backend `/app/models` | 서빙 가중치 |
| `./backend/logs` | backend `/app/logs` | 앱 로그 |
| `./data/feedback` · `./data/pseudo_labels` | backend `/app/data/...` | 학습 공유 데이터 |
| `./data/chroma` | backend `/app/shared/chroma` | 확인 피드백 Chroma |
| `./data/mariaDB_datas` | mariadb `/var/lib/mysql` | DB 파일 |
| `./data/mariaDB_backups` | mariadb-backup `/backups` | 덤프 |
| `./data/caddy/*` | caddy | 인증서 · 계정 키 (Git 제외) |

### backend 컨테이너가 `.env`를 덮어쓰는 값

호스트 도구는 `.env`의 `localhost` · 호스트 포트를 그대로 쓰고, backend 컨테이너는 Docker 내부 DNS를 쓰도록 Compose가 덮어쓴다.

| 키 | 컨테이너 값 |
|----|-------------|
| `DB_DIALECT` | `mariadb` (`DOCKER_DB_DIALECT`로 바꾸면 SQLite `data/cutnkeep.db` — 호스트 백엔드와 **다른 파일**) |
| `MARIADB_HOST` · `MARIADB_PORT` | `mariadb` · `3306` |
| `LEARNING_DB_FALLBACK_SQLITE` | `false` — 컨테이너에서는 실패를 드러낸다 |
| `REDIS_URL` | `redis://redis:6379/0` |
| `LLM_BASE_URL` | `DOCKER_LLM_BASE_URL` (기본 `http://host.docker.internal:11434`, 운영은 `http://172.18.0.1:11434`) |
| `TRUSTED_PROXIES` | `172.16.0.0/12` — nginx가 넘기는 `X-Real-IP`를 믿는 대역 |

처음 MariaDB로 바꾸면 옛 SQLite(`data/cutnkeep.db`)의 회원 · 작업을 기동 시 한 번 옮긴다 (`backend/app/db/sqlite_import.py`, 옛 파일은 지우지 않는다).

---

## 3. 이 폴더의 파일

```text
docker/
├── mariadb/
│   ├── conf.d/99-local.cnf          skip_ssl — SSL · GSS 없이 비밀번호만
│   ├── initdb.d/01-password-only.sh 처음 기동할 때 계정 · 권한
│   ├── backup/backup.sh             mariadb-backup 서비스의 덤프 스크립트
│   └── README.md                    접속 · 초기화 · 백업 · 옮기기
├── caddy/Caddyfile                  HTTPS · 보안 헤더 · Worker 비밀 값 검사
└── nginx/realip-behind-caddy.conf   Caddy 뒤에서 실제 접속 IP 쓰기
```

| 파일 | 하는 일 |
|------|---------|
| `caddy/Caddyfile` | HSTS · `Server` 헤더 제거. Cloudflare Worker가 `X-Cnk-Edge`에 `EDGE_SECRET`을 실어 보낸 경우에만 `X-Cnk-Real-IP`를 실제 사용자 IP로 믿고, 아니면 접속한 주소를 쓴다. 두 헤더는 백엔드에 넘기기 전에 지운다 |
| `nginx/realip-behind-caddy.conf` | HTTPS 모드에서만 frontend nginx에 끼워 넣는 설정 — Caddy가 넘긴 실제 IP를 쓰게 |
| `mariadb/*` | → [`mariadb/README.md`](./mariadb/README.md) |

---

## 4. 자주 하는 일

```bash
docker compose -p cut_and_keep ps                          # 상태
docker compose -p cut_and_keep logs -f backend             # 백엔드 로그
docker compose -p cut_and_keep down                        # 중지 (DB 데이터 유지)

# 호스트에서 uvicorn 을 이미 띄워 8000 이 차 있을 때 — 호스트 백엔드를 죽이지 않는다
BACKEND_PORT=8001 docker compose -p cut_and_keep --env-file .env up -d

# 가벼운 ONNX 이미지 (이미지 약 2.8GB → 약 1.1GB)
SEG_RUNTIME=onnx docker compose -p cut_and_keep --env-file .env up -d --build backend   # YOLO_MODEL_PATH=models/yolo26m-seg.onnx

# 개발용 메일함 — .env: SMTP_HOST=mailpit · SMTP_PORT=1025 · SMTP_STARTTLS=false · SMTP_SSL=false
docker compose -p cut_and_keep --env-file .env --profile mail up -d mailpit    # http://127.0.0.1:8025

# 배치를 Redis 워커로
BATCH_USE_CELERY=true docker compose -p cut_and_keep --env-file .env --profile phase2 up -d backend celery_worker
```

- **DB 초기화**는 `down` 후 `data/mariaDB_datas/` 폴더를 지운다. bind mount라 `down -v`로는 지워지지 않는다 → [`mariadb/README.md`](./mariadb/README.md)
- **운영 서버**에서는 전체 `up`을 하지 않는다. 개발용 Adminer까지 뜬다. 서비스를 지정한다.
- `.env`를 바꾼 뒤 backend 컨테이너를 다시 만들면 IP가 바뀐다. frontend nginx는 Docker DNS를 10초마다 다시 찾아 따라간다 ([`docs/repeater/nginx-backend-502.md`](../docs/repeater/nginx-backend-502.md)).

---

## 5. Compose 밖에 있는 것

| 항목 | 이유 |
|------|------|
| 운영 콘솔 (`console/`) | 공개하지 않는다. 관리자 PC에서 `npm run dev`(:5174) |
| Ollama | 로컬은 호스트 Ollama, 운영은 PC의 Ollama를 터널로 — 서버에 모델을 받지 않는다 |
| 포트폴리오 사이트 | Vercel + PC의 Flask ([`Portfolio/`](../Portfolio/README.md)) |

---

## 관련 문서

- [`docs/guidance/docker-run.md`](../docs/guidance/docker-run.md) — Docker 실행 가이드
- [`docs/guidance/https-deploy.md`](../docs/guidance/https-deploy.md) — HTTPS 배포
- [`docs/guidance/ollama-server.md`](../docs/guidance/ollama-server.md) — 서버가 PC의 Ollama 쓰기
- [`docs/guidance/gpu-deploy.md`](../docs/guidance/gpu-deploy.md) — GPU 서버
- [`docs/web_management/ports-inventory.md`](../docs/web_management/ports-inventory.md) — 포트 목록
- [`docs/HANDOVER.md`](../docs/HANDOVER.md) — 운영 서버 갱신 명령
