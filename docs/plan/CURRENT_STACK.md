# 컷앤킵 — 현재 스택 스냅샷

**기준 브랜치:** `develop`  
**스냅샷 일자:** 2026-10-11 (해석 모델 고르기 · 영상 추적 · 카메라 이동 지우기 · 실제 영상 검증 · LoRA 조합형 재학습 · GPU 오버레이 · 배포 도구 · 의존성 보안 업데이트 반영)  
**목적:** 추가·수정·제외된 구성을 한곳에 모아, 다른 문서가 어긋나지 않게 한다.

---

## 1. 앱 · 포트

| 구성 | 로컬 개발 | Docker (`-p cut_and_keep`) |
|------|-----------|----------------------------|
| Backend FastAPI | `:8000` | **`127.0.0.1:${BACKEND_PORT:-8000}`** (호스트에서 uvicorn 을 따로 띄우면 `BACKEND_PORT=8001`) |
| Frontend (사용자) | Vite 7 `:5173` | nginx **`:80` — 유일한 공개 포트** (보안 헤더 · 영상/GIF 85MB · 600초 · 사진 300초) |
| Console (운영) | Vite 7 `:5174` | **Compose 미포함** → 로컬만. 콘솔 API 는 관리자 로그인(`CONSOLE_ADMINS`) 또는 서버 PC |
| MariaDB | (선택) 호스트 클라이언트 | **`127.0.0.1:${MARIADB_PORT}`** (예: 3309) → 컨테이너 `3306` |
| Redis | — | **`127.0.0.1:6380`** → 컨테이너 `6379` |
| Adminer | — | **`127.0.0.1:8081`** (Server=`mariadb`) |

내부 포트는 `BIND_HOST`(기본 127.0.0.1)에만 열린다 — 다른 기기에서 직접 열 때만 `0.0.0.0`. 점검표: [`security.md`](../guidance/security.md)

네트워크 이름: `cut_and_keep_net`  
프로젝트 이름: **`cut_and_keep`** (구 `cutnkeep` 스택과 중복 금지)

---

## 2. 데이터베이스

| 항목 | 현재 |
|------|------|
| 서비스 DB | **Docker: MariaDB**(학습 DB 와 같은 데이터베이스, 처음 전환 시 옛 SQLite 를 자동으로 옮김) · 호스트 개발: SQLite `backend/data/cutnkeep.host.db` (users · auth_* · jobs · batch_jobs) |
| 백업 | MariaDB: `mariadb-backup` 서비스가 24시간마다 `data/mariaDB_backups/*.sql.gz`, 7일 보관 (복구 확인됨) · SQLite(호스트): `backend/data/backups/` |
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
| **루트** `requirements.docker.txt` | Docker 런타임 공통 (FastAPI 0.143 · starlette 1.7 · LangGraph 1.2 · langchain-core 1.6 · Pillow 12.3 — 2026-10-10 취약점 0건, [`security.md`](../guidance/security.md) 5절). 빌드 인자 `LLM_LORA`(LoRA 패키지) · `TORCH_INDEX`(cpu · cu128 · cu130). 세그는 `backend/Dockerfile` 의 `SEG_RUNTIME`: `ultralytics`(CPU torch, 약 2.8GB) 또는 `onnx`(onnxruntime 만, 약 1.1GB). 검증은 `docs/plan/ONNX_INFERENCE.md` |
| `training/requirements-training.txt` | 학습 venv (torch 는 로컬 wheel, 원격 자동 대용량 금지 정책) |
| ~~`backend/requirements*.txt`~~ | **제거됨** (루트로 이전) |

Backend Dockerfile: **context = 저장소 루트**, `dockerfile: backend/Dockerfile`

---

## 4. 비전 · LLM

| 항목 | 현재 기본 |
|------|-----------|
| 세그 | **YOLO26m-seg** — 서빙 `backend/models/yolo26m-seg.pt` / `.onnx`, 원본·후보 루트 `models/`. ONNX 경로는 `backend/app/utils/onnx_utils.py` (torch·ultralytics 불필요) |
| 탐지 실험 | `yolo26s.pt` (서비스 본선 아님) |
| 해석 모델 고르기 | 작업실 처리하기 옆 상자(사진 · GIF · 영상): Ollama `gemma4:e4b`(기본) · `gemma4:12b` · `qwen3.8:27b`, 서버에 설치되지 않은 모델은 "미적용" — `GET /api/v1/llm/models`, 폼 `llm_model`, `services/llm_models.py`. `LLM_PROVIDER` 가 ollama 일 때만 ([`llm-and-vision.md`](../guidance/llm-and-vision.md)) |
| LLM 설정 | `LLM_PROVIDER` — 기본 Ollama `gemma4:e4b`, 선택 `lora`(Qwen2.5-1.5B 어댑터)·openai·gemini. 실패 시 휴리스틱. **GPU 오버레이는 `lora`** (283문장 94.7% · Ollama 체인 85.2%, [`parser-compare-20261009.md`](../vaildates/parser-compare-20261009.md)) · 혼합 `PROMPT_SECOND_OPINION` |
| 프롬프트 규격 | `services/prompt_spec.py` — target·effect(`remove_object` = 지우기)·`selector`(위치·순서·개수·색 속성) |
| 프롬프트 RAG | `services/prompt_rag.py` — 사용자 교정·좋아요 중 비슷한 문장을 LLM 예시로 (글자 n-gram TF-IDF, `PROMPT_RAG_*`) |
| 해석 체인 | `PROMPT_CHAIN=langchain`(기본) — LLM 답과 키워드 파서(`heuristic_targets.py`)가 다르면 최대 3번 물어 다수결 (`services/prompt_chain.py`) |
| 인스턴스 선택 | `services/instance_selector.py` — 같은 클래스 중 특정 인스턴스 (학습 아닌 규칙) |
| 마스크 처리 | 다른 인스턴스 몫 덜어내기 `MASK_EXCLUSIVE=subtract` · GrabCut 끔 · CLAHE 끔 (지정하지 않은 대상이 섞이는 문제 — `docs/vaildates/leak-diagnosis-20261008.md`) |
| 배경 덩어리 | SegFormer ADE20K ONNX — 건물 · 하늘 · 도로 등 14종 (`services/stuff_segmentation.py`) |
| 대상 지우기 | 사진: 학습형 **LaMa** ONNX (`backend/models/lama_fp32.onnx`, 없으면 Telea, `MODEL_AUTO_DOWNLOAD` 로 자동 받기) · 영상·GIF: 다른 프레임에서 보인 **배경판**(고정 카메라 · 프레임 맞춤, 시간 중앙값 · 밝기 맞춤) → 맞지 않으면 Telea (`VIDEO_REMOVE_MODE`, `services/video_inpaint.py`) |
| 영상 · GIF | 영상: 프레임마다 처리 → H.264 mp4, 광학 흐름 스무딩 · GIF: 프레임마다 처리 → 투명 GIF(경계 매트 `matte`) + 부드러운 경계 WebP. 위치 · 순서 · 개수로 고른 대상은 프레임 사이 추적(`VIDEO_TRACK_INSTANCES`, `services/instance_tracker.py`). 회원은 작업 기록(`jobs.kind`)에 남음 — 실제 영상 검증 [`davis-real-video-20261010.md`](../vaildates/davis-real-video-20261010.md) |
| 파이프라인 실행 | LangGraph 1.2 · 스레드풀 실행 · 재시도 시 조건 변경 + 최선 시도 채택 · 기동 시 모델 워밍업 (`PRELOAD_MODELS`) · `meta.timings` ([`WORKFLOW.md`](../WORKFLOW.md)) |
| 계정 | `/api/v1/auth/*` — scrypt 해시 · HttpOnly 세션 쿠키 · 이메일 코드 재설정. SMTP 미설정 시 메일은 로그에만 ([`auth.md`](../guidance/auth.md)) |
| 접근 정책 | 비로그인: 처리·다운로드만(저장 없음, IP 별 분당 한도) / 회원: 저장·작업 기록(사진·영상·GIF)·피드백·배치(본인 것만) / 콘솔 API: 관리자 로그인 또는 서버 PC |
| 보관 · 정리 | 업로드 파일은 `FILE_RETENTION_HOURS`(24) 뒤 백엔드가 `FILE_CLEANUP_MINUTES`(60)마다 자동 삭제 · 실패 · 확신 낮은 요청의 사진은 `FEEDBACK_IMAGE_RETENTION_DAYS`(30) 뒤, 계정 삭제 시 바로 |
| 학습 | `training/` — `train_segment.py` 본선, `env_cuda.ps1` / `setup_cuda_env.ps1` |

문서: `docs/plan/AI_MODEL_STRATEGY.md`, `YOLO26S_DEFAULT.md`, `training/README.md`

---

## 5. Docker Compose 서비스 (현재)

| 서비스 | 비고 |
|--------|------|
| `backend` | env_file `.env` + DB/Redis/LLM 오버라이드. 빌드 `SEG_RUNTIME=ultralytics`(기본) 또는 `onnx` |
| `frontend` | nginx :80. 로컬 개발 도구는 Vite **7** / Vitest **5** (`frontend/`, `console/`) |
| `mariadb` | 공식 11, password + skip_ssl |
| `redis` | 127.0.0.1:6380 |
| `adminer` | 127.0.0.1:8081 |
| `celery_worker` | 프로필 `phase2` — 배치를 Redis 워커로 넘길 때만 (`BATCH_USE_CELERY=true`) |
| `mariadb-backup` | MariaDB 자동 덤프 (서비스 + 학습 DB) |
| `mailpit` | 프로필 `mail` — 개발용 메일 받은편지함 `127.0.0.1:8025` |
| `caddy` | `docker-compose.https.yml` 을 겹칠 때만 — HTTPS 인증서 · 80/443 |
| (GPU) `backend` · `celery_worker` | `docker-compose.gpu.yml` 을 겹칠 때만 — 이미지 `cut_and_keep-backend-gpu`(CUDA torch `GPU_TORCH_INDEX` cu128 기본 · cu130, LoRA 패키지), NVIDIA GPU 예약, 문장 해석 LoRA ([`gpu-deploy.md`](../guidance/gpu-deploy.md)) |
| ~~GSS 커스텀 MariaDB 이미지~~ | **제외** |

Backend 컨테이너 오버라이드 예:

- `REDIS_URL=redis://redis:6379/0`
- `LLM_BASE_URL=http://host.docker.internal:11434` (또는 `DOCKER_LLM_BASE_URL`)
- `DB_DIALECT=mariadb` (서비스 DB, `DOCKER_DB_DIALECT=sqlite` 로 되돌림) · 옛 SQLite 는 `SERVICE_DB_IMPORT_FROM` 에서 한 번 옮김
- `TRUSTED_PROXIES=172.16.0.0/12` (nginx 가 넘기는 `X-Real-IP` 로 비로그인 한도를 사람마다)

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
| 서비스 런타임 | `backend/data/` | `uploads/`, `cutnkeep.db`(Docker) · `cutnkeep.host.db`(호스트), `backups/` | `backend/` 상대 |
| 서비스 런타임 | `backend/models/` | 지금 서빙 중인 활성 가중치 (YOLO · SegFormer · LaMa · LoRA) | `backend/` 상대 |
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
- [ ] YOLO **m-seg** 기본
- [ ] 내부 포트 **127.0.0.1** 바인딩 · 공개는 frontend :80
- [ ] 작업 종류(사진 · 영상 · GIF) · LaMa · 자동 정리 · 자동 백업
- [ ] 커밋 기록 경로 **branchs/commits**
- [ ] 오버레이 **https · gpu**, 배포 도구 `make_prod_env` · `deploy_check` · `models_bundle` ([`DEPLOYMENT.md`](../DEPLOYMENT.md))
- [ ] 해석 모델 목록(`llm_models.CATALOG`)과 서버 Ollama 에 설치된 모델 — 큰 모델은 첫 호출이 느리다(nginx 300초)
- [ ] 의존성 취약점 점검 결과 ([`security.md`](../guidance/security.md) 5절)
- [ ] Console Compose 미포함
- [ ] 런타임(`backend/`) · 학습 공유(루트) 폴더 분리

이 스냅샷과 충돌하는 문구가 있으면 **이 파일을 우선**하고 해당 문서를 고친다.
