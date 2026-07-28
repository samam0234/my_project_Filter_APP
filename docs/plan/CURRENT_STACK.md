# 컷앤킵 — 현재 스택 스냅샷

**기준 브랜치:** `develop`  
**스냅샷 일자:** 2026-07-28  
**목적:** 추가·수정·제외된 구성을 한곳에 모아, 다른 문서가 어긋나지 않게 한다.

---

## 1. 앱 · 포트

| 구성 | 로컬 개발 | Docker (`-p cut_and_keep`) |
|------|-----------|----------------------------|
| Backend FastAPI | `:8000` | `:8000` |
| Frontend (사용자) | Vite `:5173` | nginx `:80` |
| Console (운영) | Vite `:5174` | **Compose 미포함** → 로컬만 |
| MariaDB | (선택) 호스트 클라이언트 | 호스트 **`${MARIADB_PORT}`** (예: **3309**) → 컨테이너 `3306` |
| Redis | — | 호스트 **6380** → 컨테이너 `6379` |
| Adminer | — | **`:8081`** (Server=`mariadb`) |

네트워크 이름: `cut_and_keep_net`  
프로젝트 이름: **`cut_and_keep`** (구 `cutnkeep` 스택과 중복 금지)

---

## 2. 데이터베이스

| 항목 | 현재 |
|------|------|
| 로컬 기본 | `DB_DIALECT=sqlite` → `data/cutnkeep.db` |
| Docker backend | compose 가 **`DB_DIALECT=mariadb`**, `MARIADB_HOST=mariadb`, `PORT=3306` 강제 |
| 이미지 | 공식 **`mariadb:11`** (GSS 커스텀 이미지 **제거됨**) |
| 인증 | **비밀번호만** (`mysql_native_password`). GSS-API **미사용** |
| SSL | 서버 **`skip_ssl`** (로컬 Docker) |
| 계정 | `.env` 의 `MARIADB_USER` / `PASSWORD` / `DATABASE` + `MYSQL_ROOT_PASSWORD` |
| 볼륨 | `cut_and_keep_mariadb_data` — 계정 변경 시 `down -v` 후 재생성 |
| 설정 파일 | `docker/mariadb/conf.d/99-local.cnf`, `initdb.d/01-password-only.sh` |

### 접속 요약

| 도구 | Host | Port | User |
|------|------|------|------|
| DBeaver (호스트) | `127.0.0.1` | `.env` `MARIADB_PORT` | `.env` `MARIADB_*` |
| Adminer | Server=`mariadb` | (내부) | 동일 |
| backend 컨테이너 | `mariadb` | `3306` | compose 주입 |

**제외·하지 말 것:** DBeaver GSS/Kerberos, 호스트로 `172.18.0.x` 사용, detect 전용 `.pt` 를 세그 경로에 배치.

상세: `docs/plan/DATABASE.md`, `docker/mariadb/README.md`

---

## 3. Python 의존성

| 파일 | 용도 |
|------|------|
| **루트** `requirements.txt` | 로컬 backend 풀스택 |
| **루트** `requirements.docker.txt` | Docker 경량 이미지 (YOLO/torch 없음 → stub 세그 가능) |
| `training/requirements-training.txt` | 학습 venv (torch 는 로컬 wheel, 원격 자동 대용량 금지 정책) |
| ~~`backend/requirements*.txt`~~ | **제거됨** (루트로 이전) |

Backend Dockerfile: **context = 저장소 루트**, `dockerfile: backend/Dockerfile`

---

## 4. 비전 · LLM

| 항목 | 현재 기본 |
|------|-----------|
| 세그 | **YOLO26s-seg** (`models/yolo26s-seg.pt` / `.onnx`) |
| 탐지 실험 | `yolo26s.pt` (서비스 본선 아님) |
| LLM 설정 | Ollama `gemma4:e4b` (Settings). **프롬프트 노드는 휴리스틱 기본**, LLM 연동은 수동 구현 지점 |
| 학습 | `training/` — `train_segment.py` 본선, `env_cuda.ps1` / `setup_cuda_env.ps1` |

문서: `docs/plan/AI_MODEL_STRATEGY.md`, `YOLO26S_DEFAULT.md`, `training/README.md`

---

## 5. Docker Compose 서비스 (현재)

| 서비스 | 비고 |
|--------|------|
| `backend` | env_file `.env` + DB/Redis/LLM 오버라이드 |
| `frontend` | nginx :80 |
| `mariadb` | 공식 11, password + skip_ssl |
| `redis` | 6380:6379 |
| `adminer` | 8081 |
| ~~celery_worker~~ | 주석/미포함 (Phase 2) |
| ~~GSS 커스텀 MariaDB 이미지~~ | **제외** |

Backend 컨테이너 오버라이드 예:

- `REDIS_URL=redis://redis:6379/0`
- `LLM_BASE_URL=http://host.docker.internal:11434` (또는 `DOCKER_LLM_BASE_URL`)

---

## 6. 테스트 · 학습

| 구역 | 내용 |
|------|------|
| `tests/` | pytest unit / structure / smoke |
| `pytest.ini` | 루트 |
| `training/` | YOLO + LoRA 스크립트, datasets/outputs gitignore |

---

## 7. Git · 문서 규칙

| 항목 | 현재 |
|------|------|
| 작업 브랜치 | `feature/*` |
| 통합 | `develop` / `main`, **`merge --no-ff`** |
| 커밋 메시지 | type/scope 영어 · 제목·본문·바닥글 **한국어** |
| 커밋 기록 | **`docs/branchs/commits/` 필수** · `docs/commits/` **금지** |
| 기본 원격 브랜치 | `origin/HEAD` → **develop** |

---

## 8. 루트에 있는 것 (혼동 주의)

| 경로 | 역할 |
|------|------|
| `README.md` | **저장소 홈 소개 (컷앤킵)** |
| `.github/Read_for_we.md` | GitHub 폴더 내부 안내 (구 README — 홈 아님) |
| `.agents/`, `.grok/`, `.claude/` 등 | 에이전트 도구 설정 (앱 런타임 아님) |
| `AGENTS.md` | 에이전트 프로젝트 규칙 요약 |

---

## 9. 문서 갱신 시 체크

- [ ] 포트 표에 **Adminer 8081**, **MariaDB 호스트 포트 env**, **Redis 6380**
- [ ] MariaDB **비밀번호 전용 · GSS/SSL 없음**
- [ ] requirements **루트** 위치
- [ ] YOLO **s-seg** 기본
- [ ] 커밋 기록 경로 **branchs/commits**
- [ ] Console Compose 미포함

이 스냅샷과 충돌하는 문구가 있으면 **이 파일을 우선**하고 해당 문서를 고친다.
