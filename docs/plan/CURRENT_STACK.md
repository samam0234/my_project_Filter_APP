# 컷앤킵 — 현재 스택 스냅샷

**기준 브랜치:** `develop`  
**스냅샷 일자:** 2026-10-06 (ONNX 직접 추론 · YOLO26m-seg · vite 7 반영)  
**목적:** 추가·수정·제외된 구성을 한곳에 모아, 다른 문서가 어긋나지 않게 한다.

---

## 1. 앱 · 포트

| 구성 | 로컬 개발 | Docker (`-p cut_and_keep`) |
|------|-----------|----------------------------|
| Backend FastAPI | `:8000` | `:8000` |
| Frontend (사용자) | Vite 7 `:5173` | nginx `:80` |
| Console (운영) | Vite 7 `:5174` | **Compose 미포함** → 로컬만 (콘솔 API 는 loopback 요청만 허용) |
| MariaDB | (선택) 호스트 클라이언트 | 호스트 **`${MARIADB_PORT}`** (예: **3309**) → 컨테이너 `3306` |
| Redis | — | 호스트 **6380** → 컨테이너 `6379` |
| Adminer | — | **`:8081`** (Server=`mariadb`) |

네트워크 이름: `cut_and_keep_net`  
프로젝트 이름: **`cut_and_keep`** (구 `cutnkeep` 스택과 중복 금지)

---

## 2. 데이터베이스

| 항목 | 현재 |
|------|------|
| 서비스 DB | `DB_DIALECT=sqlite` → `backend/data/cutnkeep.db` (users · auth_* · jobs · batch_jobs) — 로컬·Docker 공통 |
| 학습 DB | `LEARNING_DB_DIALECT=mariadb` (feedbacks · learning_samples, 경로·라벨만). 호스트는 `127.0.0.1:MARIADB_PORT`, 꺼져 있으면 `backend/data/learning.db` fallback. Docker backend 는 `mariadb:3306` 강제 ([`DATABASE.md`](DATABASE.md)) |
| 이미지 | 공식 **`mariadb:11`** (GSS 커스텀 이미지 **제거됨**) |
| 인증 | **비밀번호만** (`mysql_native_password`). GSS-API **미사용** |
| SSL | 서버 **`skip_ssl`** (로컬 Docker) |
| 계정 | `.env` 의 `MARIADB_USER` / `PASSWORD` / `DATABASE` + `MYSQL_ROOT_PASSWORD` |
| 데이터 | 호스트 **`data/mariaDB_datas/`** (bind mount → `/var/lib/mysql`, git 제외). 계정 변경·초기화는 `down` 후 폴더 삭제 (`down -v` 로는 안 지워짐) |
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
| **루트** `requirements.docker.txt` | Docker 런타임 공통 (LangGraph 포함). 세그는 `backend/Dockerfile` 의 `SEG_RUNTIME`: `ultralytics`(CPU torch, 약 2.8GB) 또는 `onnx`(onnxruntime 만, 약 1.1GB). 검증은 `docs/plan/ONNX_INFERENCE.md` |
| `training/requirements-training.txt` | 학습 venv (torch 는 로컬 wheel, 원격 자동 대용량 금지 정책) |
| ~~`backend/requirements*.txt`~~ | **제거됨** (루트로 이전) |

Backend Dockerfile: **context = 저장소 루트**, `dockerfile: backend/Dockerfile`

---

## 4. 비전 · LLM

| 항목 | 현재 기본 |
|------|-----------|
| 세그 | **YOLO26m-seg** — 서빙 `backend/models/yolo26m-seg.pt` / `.onnx`, 원본·후보 루트 `models/`. ONNX 경로는 `backend/app/utils/onnx_utils.py` (torch·ultralytics 불필요) |
| 탐지 실험 | `yolo26s.pt` (서비스 본선 아님) |
| LLM 설정 | `LLM_PROVIDER` — 기본 Ollama `gemma4:e4b`, 선택 `lora`(Qwen2.5-1.5B 어댑터)·openai·gemini. 실패 시 휴리스틱 |
| 프롬프트 규격 | `services/prompt_spec.py` — target·effect(`remove_object` = 지우기)·`selector`(위치·순서·개수·색 속성) |
| 프롬프트 RAG | `services/prompt_rag.py` — 사용자 교정·좋아요 중 비슷한 문장을 LLM 예시로 (글자 n-gram TF-IDF, `PROMPT_RAG_*`) |
| 인스턴스 선택 | `services/instance_selector.py` — 같은 클래스 중 특정 인스턴스 (학습 아닌 규칙) |
| 파이프라인 실행 | LangGraph 0.2 · 스레드풀 실행 · 재시도 시 조건 변경 + 최선 시도 채택 · 기동 시 모델 워밍업 (`PRELOAD_MODELS`) · `meta.timings` ([`WORKFLOW.md`](../WORKFLOW.md)) |
| 계정 | `/api/v1/auth/*` — scrypt 해시 · HttpOnly 세션 쿠키 · 이메일 코드 재설정. SMTP 미설정 시 메일은 로그에만 ([`auth.md`](../guidance/auth.md)) |
| 접근 정책 | 비로그인: 처리·다운로드만(저장 없음) / 회원: 저장·작업 기록·피드백·배치(본인 것만) / 콘솔 API: 서버 PC 만 |
| 학습 | `training/` — `train_segment.py` 본선, `env_cuda.ps1` / `setup_cuda_env.ps1` |

문서: `docs/plan/AI_MODEL_STRATEGY.md`, `YOLO26S_DEFAULT.md`, `training/README.md`

---

## 5. Docker Compose 서비스 (현재)

| 서비스 | 비고 |
|--------|------|
| `backend` | env_file `.env` + DB/Redis/LLM 오버라이드. 빌드 `SEG_RUNTIME=ultralytics`(기본) 또는 `onnx` |
| `frontend` | nginx :80. 로컬 개발 도구는 Vite **7** / Vitest **5** (`frontend/`, `console/`) |
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

## 9. 런타임 · 학습 폴더 분리

| 역할 | 경로 | 내용 | 기준 |
|------|------|------|------|
| 서비스 런타임 | `backend/data/` | `uploads/`, `cutnkeep.db` | `backend/` 상대 |
| 서비스 런타임 | `backend/models/` | 지금 서빙 중인 활성 가중치 | `backend/` 상대 |
| 서비스 런타임 | `backend/logs/` | `app_YYYY-MM-DD.log` (자정 회전, 14일) | `backend/` 상대 |
| 학습 공유 | `data/` | `feedback/`, `pseudo_labels/` | 루트 상대 |
| 학습 공유 | `models/` | 모델 원본·후보·LoRA 어댑터 보관소 | 루트 상대 |
| 학습 공유 | `logs/` | 학습·스크립트 로그 | 루트 상대 |

- 코드: `Settings.resolve_runtime_path` / `resolve_shared_path` (`backend/app/core/config.py`)
- 배포: `training/yolo/apply_best.py` → `backend/models/`
- Docker: `./backend/{data,models,logs}` → `/app/{data,models,logs}`, `./data/{feedback,pseudo_labels}` → `/app/data/{feedback,pseudo_labels}`

---

## 10. 문서 갱신 시 체크

- [ ] 포트 표에 **Adminer 8081**, **MariaDB 호스트 포트 env**, **Redis 6380**
- [ ] MariaDB **비밀번호 전용 · GSS/SSL 없음**
- [ ] requirements **루트** 위치
- [ ] YOLO **s-seg** 기본
- [ ] 커밋 기록 경로 **branchs/commits**
- [ ] Console Compose 미포함
- [ ] 런타임(`backend/`) · 학습 공유(루트) 폴더 분리

이 스냅샷과 충돌하는 문구가 있으면 **이 파일을 우선**하고 해당 문서를 고친다.
