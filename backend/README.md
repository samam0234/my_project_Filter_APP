# backend — 컷앤킵 FastAPI 서버

> 문장을 받아 구조로 바꾸고, 대상 마스크를 만들고, 효과를 적용하고, 회원에게만 기록하는 서버.

컷앤킵의 API · 이미지 / 영상 파이프라인 · 계정 · DB를 맡는다. 사용자 앱([`frontend/`](../frontend/README.md))과 운영 콘솔([`console/`](../console/README.md))은 모두 이 서버의 `/api/v1`만 호출한다.

| 항목 | 내용 |
|------|------|
| 포트 | 8000 (공개 서버에서는 Caddy 443 → nginx 뒤) |
| 기술 | Python 3.11 · FastAPI 0.143 · Starlette 1.7 · Pydantic 2 · Uvicorn · SQLAlchemy 2 · loguru · OpenCV |
| 비전 | YOLO26m-seg (Ultralytics `.pt` 또는 ONNX Runtime) · SegFormer ADE20K · LaMa |
| 해석 | Ollama (기본 `gemma4:e4b`) · 선택 LoRA · OpenAI · Gemini · 키워드 파서 |
| 흐름 | LangGraph 1.2 · LangChain Core |
| DB | 서비스 DB · 학습 DB 분리 — Docker는 MariaDB 11, 호스트 개발은 SQLite |
| 테스트 | pytest **505개** (2026-10-12, 저장소 루트 `tests/`) |

---

## 1. 요청 하나가 지나가는 길

```text
POST /api/v1/upload (file, prompt, llm_model)
  │
  ├─ core/security.py   확장자 · MIME · 파일 시그니처 · 해상도(압축 폭탄) 검사
  ├─ core/ratelimit.py  비로그인 IP / 회원 계정별 속도 제한
  │
  └─ workflows/graph.py (LangGraph)
        prompt_analyzer   문장 → ParsedPrompt (LLM + 키워드 파서 다수결, RAG 예시)
        preprocessor      리사이즈 (CLAHE 기본 끔)
        segmentor         YOLO26m-seg 인스턴스 + SegFormer 배경 덩어리 → 선택자로 고르기 → 겹침 덜어내기
        validator         ok / fallback / failed  ── 실패에 가까우면 조건을 바꿔 segmentor 로 한 번 더
        effect_applier    remove_bg · blur · crop · remove_object(LaMa → Telea)
        feedback_collector 회원 · 실패 사례를 학습 후보로
  │
  ├─ 비로그인  → 저장 없이 data URL 로 응답
  └─ 회원     → backend/data/uploads/{job_id}/ 저장 + jobs 기록 (24시간 뒤 자동 삭제)
```

- **재시도:** 검증 결과가 실패에 가까우면 전처리 조건을 반대로 하고 신뢰도 기준을 낮춰 한 번 더 찾는다. 더 나쁜 마스크면 첫 시도를 유지한다.
- **정직한 실패:** 요청 대상이 라벨에 없으면 가짜 마스크로 속이지 않고 "요청한 대상을 찾지 못함"과 그때 보인 라벨을 알려 준다.
- **영상 · GIF:** 프레임마다 같은 규칙을 적용한다. 위치나 순서로 고른 대상은 첫 프레임의 그 대상을 끝까지 따라가고(`instance_tracker`), 광학 흐름으로 마스크 흔들림을 줄인다. 지우기는 다른 프레임에서 보인 배경판으로 메운다(`video_inpaint`).

### 효과

| 효과 | 코드 값 | 결과 |
|------|---------|------|
| 남기고 배경 제거 | `remove_bg` | 투명 PNG · GIF · WebP |
| 배경 블러 | `blur` | 강도 0~100. 문장에 숫자가 없으면 15 |
| 크롭 | `crop` | 대상 주변으로 자름 |
| 대상 지우기 | `remove_object` | 사진은 LaMa, 없으면 Telea. 영상은 배경판 |

인스턴스 선택은 **규칙**이다 — 위치 · 순서 · 개수 · 크기 · 색과 부위. 지정하지 않은 대상이 섞이지 않게 다른 인스턴스 영역을 빼는 것(`MASK_EXCLUSIVE=subtract`)이 기본이고, GrabCut과 CLAHE는 섞임 때문에 기본으로 꺼 두었다 ([`docs/vaildates/leak-diagnosis-20261008.md`](../docs/vaildates/leak-diagnosis-20261008.md)).

---

## 2. 계층

계층은 고정이다.

| 계층 | 경로 | 책임 | 하지 않는 것 |
|------|------|------|--------------|
| Router | `app/routers/` | HTTP · 권한 · 응답 | SQL을 직접 쓰지 않음 |
| Schema | `app/schemas/` | Pydantic 요청 / 응답 DTO | ORM 모델과 섞지 않음 |
| Service · Workflow | `app/services/` · `app/workflows/` | 처리 · 파일 · LangGraph | |
| Repository | `app/repositories/` | SQL | OpenCV와 LLM을 모름 |
| Model | `app/models/` | 테이블 (SQLAlchemy ORM) | |
| DB | `app/db/` | 엔진 · 세션 · 학습 DB · SQLite 가져오기 | |
| Core | `app/core/` | 설정 · 보안 · 접근 · 속도 제한 · 기동 점검 | |

```text
backend/
├── app/
│   ├── main.py            FastAPI 앱 · CORS · lifespan · /health
│   ├── core/              config · security · access · deps · passwords · ratelimit · preflight · constants
│   ├── routers/           auth · upload · gif · video · jobs · feedback · batch · llm · chat · console
│   ├── schemas/           auth · chat · feedback · learning · request · response
│   ├── services/          파이프라인 · 계정 · 메일 · 학습 · 운영 (아래 표)
│   ├── workflows/         graph · nodes · edges · state (LangGraph)
│   ├── repositories/      user · job · batch · feedback
│   ├── models/            user · job · batch_job · feedback · learning · learning_sample
│   ├── db/                base · session · learning · sqlite_import
│   ├── tasks/             batch_tasks (Celery, 선택)
│   └── utils/             image_utils · logging · onnx_utils
├── data/                  서비스 런타임 (업로드 · 호스트 SQLite · Chroma)  → data/README.md
├── models/                서빙 중인 가중치 (Git 밖)                          → models/README.md
├── logs/                  앱 로그 app_YYYY-MM-DD.log (14일)                   → logs/README.md
└── Dockerfile             빌드 context = 저장소 루트
```

### 서비스 모듈

**문장 해석**

| 파일 | 역할 |
|------|------|
| `prompt_spec.py` | 프롬프트 규격 정본 — LLM 지시문 · LoRA 템플릿 · `normalize_parsed`. **바꾸면 LoRA를 다시 학습해야 한다** |
| `prompt_llm.py` | `LLM_PROVIDER` 분기 (ollama · openai · gemini · lora), 실패 시 `LLMError` |
| `prompt_lora.py` | LoRA 어댑터 로컬 추론 (transformers + peft, 싱글톤) |
| `prompt_chain.py` | 해석 체인 (LangChain Core) — LLM 답과 키워드 파서가 다르면 다수결 (`PROMPT_CHAIN=langchain`, `PROMPT_VOTES=3`) |
| `heuristic_targets.py` | 키워드 파서 — 어휘 + 역할 규칙(남길 것 · 뺄 것 · 지울 것). LLM이 꺼져도 동작 |
| `prompt_rag.py` | 승인된 교정 · 좋아요 · 요청 중 비슷한 문장을 LLM 예시로 (글자 2·3-gram TF-IDF) |
| `prompt_chroma.py` · `chroma_embed.py` | `backend/data/chroma`와 루트 `data/chroma`에서 확인된 문장 한 건을 더함. 임베딩 모델은 받지 않음 |
| `llm_models.py` | 고를 수 있는 Ollama 모델 목록과 설치 여부 ("미적용") |

**비전 · 효과**

| 파일 | 역할 |
|------|------|
| `segmentation.py` | YOLO-seg 인스턴스 · 대상 라벨 필터 · 라벨 별칭 · 모델이 없을 때 데모용 stub |
| `stuff_segmentation.py` | 배경 덩어리(건물 · 하늘 · 도로 등 14종) SegFormer ONNX |
| `instance_selector.py` | 같은 클래스 중 위치 · 순서 · 개수 · 크기 · 색 속성으로 선택 |
| `mask_exclusion.py` | 고른 인스턴스에서 다른 인스턴스 몫 덜어내기 · 위험 신호(`meta.leak`) |
| `validator.py` | 마스크 품질 점수 → ok / fallback / failed |
| `image_processor.py` | 전처리 (리사이즈 + CLAHE, CLAHE 기본 끔) |
| `effects.py` | 경계 다듬기 · 배경 제거 · 블러 · 크롭 · `remove_object` |
| `inpaint.py` | 학습형 인페인팅 LaMa ONNX (`models/lama_fp32.onnx`) |
| `model_fetch.py` | 없는 모델(LaMa) 받기 · SHA-256 확인 · 기동 시 백그라운드 (`MODEL_AUTO_DOWNLOAD`) |

**영상 · GIF**

| 파일 | 역할 |
|------|------|
| `video_processor.py` | 프레임 처리(`FrameRenderer` — GIF와 공용) · 광학 흐름 스무딩 · mp4 변환 · 원본 미리 보기 |
| `instance_tracker.py` | 위치 · 순서 · 개수로 고른 대상을 프레임 사이로 따라가기 (다른 사람도 같이 추적, 가려짐 대비) |
| `video_inpaint.py` | 영상 · GIF 지우기 배경판 — 고정 카메라 · 프레임 맞춤(호모그래피) · 시간 중앙값 · 밝기 맞춤, 안 맞는 프레임은 Telea |
| `gif_processor.py` | 움직이는 GIF 읽기 · 처리 · 투명 GIF / WebP 쓰기 (간격과 반복 유지) |

**계정 · 메일 · 채팅**

| 파일 | 역할 |
|------|------|
| `auth_service.py` | 가입(**이메일 인증** — 일련번호 · 대기 신청) · 로그인 잠금 · 세션 · 내 계정(이름 · 비밀번호 변경 · 탈퇴) · 아이디 찾기 · 비밀번호 재설정 |
| `mail_templates.py` · `mailer.py` | HTML + 텍스트 메일 본문 (가입 인증 · 아이디 · 재설정), SMTP 발송 (미설정이면 로그에만) |
| `chat_agent.py` | "에이전트에게 묻기" — Ollama `/api/chat`, 서버 고정 시스템 프롬프트, **대화 비저장** |

**학습 · 운영**

| 파일 | 역할 |
|------|------|
| `feedback_service.py` | 피드백 DB + `data/feedback/` 사이드카 파일 |
| `feedback_images.py` | 실패 · 확신 낮은 요청 사진 보관 기간 (`FEEDBACK_IMAGE_RETENTION_DAYS`) · 계정 삭제 때 정리 |
| `learning_catalog.py` · `learning_review.py` | 학습 후보 수집 · 콘솔 검수 |
| `retention.py` · `maintenance.py` · `db_backup.py` | 보관 기간 정리 · 주기 작업 (매시간 자동 정리 · 서비스 DB 백업) |
| `user_admin.py` · `system_status.py` | 콘솔 회원 관리 · 시스템 스냅샷 |

**Core 보조**

| 파일 | 역할 |
|------|------|
| `core/access.py` | `owned_job`(본인 작업만, 아니면 404) · `require_console`(관리자 로그인 또는 서버 PC) |
| `core/ratelimit.py` | 속도 제한. `client_ip()`는 `TRUSTED_PROXIES`에서 온 요청만 `X-Real-IP`를 믿는다 |
| `core/security.py` | 업로드 검증 — 확장자 · MIME · 시그니처 · 해상도 순 |
| `core/passwords.py` · `core/deps.py` | scrypt · 토큰 · 코드 · `current_user` |
| `core/preflight.py` | 운영(`APP_ENV=production`)에서 위험한 기본값이면 **기동을 막는다** |

---

## 3. API

접두사는 `/api/v1`이다. 운영에서는 Swagger(`/docs`)를 열지 않는다.

| 묶음 | 경로 |
|------|------|
| 상태 | `GET /health` (접두사 없음) |
| 사진 | `POST /upload` · `GET /files/{id}/before \| after \| thumb \| webp` |
| GIF | `POST /gif` (`matte` = none · light · dark) |
| 영상 | `POST /video` · `GET /video/{id}` |
| 기록 | `GET /jobs` · `GET /jobs/{id}` |
| 피드백 | `POST /feedback` |
| 배치 | `POST /batch` · `GET /batch` · `GET /batch/{id}` · `GET /batch/{id}/items/{index}/{kind}` · `GET /batch/{id}/download` |
| 계정 | `/auth/signup/start` · `/signup/verify` · `/signup/resend` · `/login` · `/logout` · `/logout-all` · `GET·PATCH·DELETE /me` · `/find-id` · `/password/request` · `/password/reset` · `/password/change` |
| 모델 | `GET /llm/models` |
| 채팅 | `POST /chat` |
| 콘솔 | `/console/me` · `jobs` · `batches` · `learning/stats` · `learning/samples`(목록 · 이미지 · 검수 · 일괄 · 삭제) · `users`(목록 · 잠금 해제 · 세션 끊기 · 삭제) · `system` · `system/cleanup` |

**접근 규칙**

- 결과 파일과 기록은 소유자가 아니면 **404**다. 없는 것과 남의 것을 구분하지 않는다.
- 비로그인 업로드는 저장 없이 data URL로 응답한다.
- 콘솔 API는 `CONSOLE_ADMINS`에 있는 아이디로 로그인했거나, `CONSOLE_REQUIRE_LOGIN=false`인 서버 PC에서만 열린다.
- 속도 제한은 비로그인 IP(사진 분당 6) · 회원 계정(분당 20)을 나눈다. Cloudflare Worker가 넘긴 실제 IP는 `EDGE_SECRET`이 맞을 때만 믿는다.
- 업로드 크기는 사진 약 20MB, 영상 80MB · 20초 · 긴 변 3840, GIF 120프레임까지다.

호출 예와 응답 형식: [`docs/guidance/api-usage.md`](../docs/guidance/api-usage.md) · [`docs/API_DOCUMENTATION.md`](../docs/API_DOCUMENTATION.md)

---

## 4. 데이터베이스

| DB | 테이블 | Docker | 호스트 개발 |
|----|--------|--------|-------------|
| 서비스 DB | `users` · `auth_sessions` · `auth_codes` · `signup_pending` · `jobs`(kind = image · video · gif) · `batch_jobs` | MariaDB (`DB_DIALECT=mariadb`) | SQLite `data/cutnkeep.host.db` |
| 학습 DB | `feedbacks` · `learning_samples` | MariaDB | MariaDB, 꺼져 있으면 SQLite `data/learning.db`로 잠시 대체 |

- 두 DB는 외래 키로 연결하지 않는다. 학습 DB가 꺼져도 서비스는 멈추지 않고, 다시 켜면 사이드카 파일과 동기화한다 (`LEARNING_SYNC_ON_START`).
- 이미지와 영상은 DB에 넣지 않는다. 경로만 기록한다.
- 스키마는 기동 시 `create_all`과 제한된 `ALTER`로 맞춘다. Alembic은 아직이다.
- 호스트에서 띄운 백엔드와 Docker 백엔드가 **같은 SQLite 파일을 쓰면 손상된 적이 있다.** 그래서 호스트는 `cutnkeep.host.db`, Docker는 MariaDB(또는 `cutnkeep.db`)로 나눴다.
- Docker에서 처음 MariaDB로 바꾸면 옛 SQLite(`data/cutnkeep.db`)의 회원 · 작업을 기동 시 한 번 옮긴다 (`db/sqlite_import.py`).

설계: [`docs/plan/DATABASE.md`](../docs/plan/DATABASE.md) · ERD: [`Portfolio/markdown/08-erd.md`](../Portfolio/markdown/08-erd.md)

---

## 5. 기동할 때 하는 일

`app/main.py`의 lifespan이 순서대로 한다.

1. 로그 설정 (`backend/logs/app_YYYY-MM-DD.log`, `LOG_RETENTION_DAYS`)
2. **기동 점검** (`core/preflight.py`) — 운영에서 위험한 기본값이면 여기서 멈춘다 (`PREFLIGHT_STRICT`)
3. 업로드 · 피드백 · 의사 라벨 폴더 생성
4. 서비스 DB 테이블 보장, 학습 DB 연결(실패하면 SQLite 대체) 후 사이드카 동기화
5. `PRELOAD_MODELS=true`면 세그 모델을 백그라운드로 올리고 빈 이미지로 한 번 추론 — 첫 요청이 약 71초에서 **약 4.5초**로 줄었다
6. 주기 작업 시작 — 보관 기간 지난 업로드 정리(`FILE_CLEANUP_MINUTES`, 매시간) · 서비스 DB 백업(`DB_BACKUP_HOURS`)
7. LaMa가 없으면 백그라운드로 받는다 (받는 동안은 Telea)

처리 중에도 `/health`는 스레드풀 때문에 바로 응답한다. YOLO 추론 자체는 잠금으로 한 번에 하나다.
`/health`의 `phase` 상수는 1로 고정이다. 스모크 테스트가 그 값을 확인한다.

---

## 6. 실행

Python 의존성은 **저장소 루트**에 있다 (`requirements.txt` · `requirements.docker.txt`).

```bash
# 저장소 루트에서
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt          # Docker 와 비슷한 경량: requirements.docker.txt

cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000   # 다른 기기에서 열 때만 0.0.0.0
```

- API 문서: http://localhost:8000/docs (개발에서만) · 상태: http://localhost:8000/health
- 환경변수: 루트 `.env` (`.env.example`에서 복사)
- 문장 해석에는 Ollama가 필요하다: `ollama pull gemma4:e4b`. 없으면 키워드 파서로 동작한다.
- 세그 가중치가 없으면 가짜 마스크(stub)로 데모만 된다 → [`models/README.md`](models/README.md)

### 자주 바꾸는 설정 (`.env`)

| 키 | 기본 | 설명 |
|----|------|------|
| `APP_ENV` | development | production이면 기동 점검이 엄격해진다 |
| `LLM_PROVIDER` · `OLLAMA_MODEL` · `LLM_BASE_URL` | ollama · `gemma4:e4b` · `http://localhost:11434` | 문장 해석 |
| `LLM_FALLBACK` | ollama | 운영은 `heuristic` — LLM이 안 되면 키워드 파서 |
| `PROMPT_CHAIN` · `PROMPT_VOTES` | langchain · 3 | 해석 다수결 |
| `PROMPT_RAG_ENABLED` · `PROMPT_RAG_MIN_SCORE` | true · 0.6 | 승인 문장 예시 (글자 n-gram) |
| `PROMPT_CHROMA_ENABLED` · `PROMPT_CHROMA_MIN_SCORE` | true · 0.55 | Chroma 확인 문장 한 건 더하기 · 이 코사인 미만은 붙이지 않음 |
| `PROMPT_CHROMA_DIR` · `PROMPT_CHROMA_SHARED_DIR` | `data/chroma` · `data/chroma` | 승인 예시 Chroma(backend/ 기준 → `backend/data/chroma`) · 확인 피드백 Chroma(루트 `data/chroma`, Docker는 `/app/shared/chroma`) |
| `YOLO_MODEL_PATH` | `models/yolo26m-seg.pt` | 세그 가중치 (`.onnx`도 됨) |
| `STUFF_SEG_ENABLED` · `INPAINT_ENGINE` | true · auto | 배경 덩어리 · 지우기 엔진 |
| `MASK_EXCLUSIVE` · `MASK_GRABCUT` · `PREPROCESS_CLAHE` | subtract · false · false | 섞임 방지 기본값 |
| `VIDEO_*` · `GIF_*` | 20초 · 80MB · 120프레임 | 영상 · GIF 한도 |
| `FILE_RETENTION_HOURS` · `FEEDBACK_IMAGE_RETENTION_DAYS` | 24 · 30 | 보관 기간 (바꾸면 처리방침 문구도 함께) |
| `DB_DIALECT` · `LEARNING_DB_DIALECT` | sqlite · mariadb | DB 종류 |
| `CONSOLE_ADMINS` · `CONSOLE_REQUIRE_LOGIN` | 비어 있음 · false | 콘솔 접근 |
| `SIGNUP_EMAIL_VERIFICATION` · `SMTP_*` | true · 비어 있음 | 가입 인증 메일 (비어 있으면 로그에만) |
| `TRUSTED_PROXIES` · `CORS_ORIGINS` | | 프록시 · 허용 출처 |

전체 목록과 설명은 `.env.example`에 있다. 운영 `.env`는 `python scripts/make_prod_env.py`로 만든다.

### Docker

```bash
docker compose -p cut_and_keep --env-file .env up -d --build backend
docker compose -p cut_and_keep logs -f backend
```

| 빌드 인자 | 값 | 설명 |
|-----------|-----|------|
| `SEG_RUNTIME` | `ultralytics`(기본) · `onnx` | `.pt` + CPU torch(이미지 약 2.8GB) 또는 onnxruntime만(약 1.1GB, `YOLO_MODEL_PATH`도 `.onnx`로) |
| `LLM_LORA` | `0`(기본) · `1` | transformers · peft 설치. CPU에서는 실사용이 안 된다 (2026-10-09 측정: 첫 로드 699초, 문장당 평균 23초) |
| `TORCH_INDEX` | `cpu`(기본) · `cu128` | GPU 서버용 (`docker-compose.gpu.yml`) |

호스트에서 uvicorn을 이미 띄워 8000이 차 있으면 `BACKEND_PORT=8001`로 피한다. 호스트 백엔드를 죽이지 않는다.

---

## 7. 테스트

```bash
# 저장소 루트에서 — venv 를 새로 만든다
python -m venv .venv && .venv/Scripts/pip install -r requirements.docker.txt -r tests/requirements-test.txt
.venv/Scripts/python -m pytest tests            # 505 passed (2026-10-12)
.venv/Scripts/python -m pytest tests/unit -q     # 단위만
```

테스트는 실제 `backend/data`를 건드리지 않는다. 메일은 가로채고, DB는 메모리로, 세그와 Ollama는 가짜로 바꾼다. 구성: [`tests/README.md`](../tests/README.md)

---

## 8. 알려진 한계

- 문장 해석이 운영자 PC의 Ollama에 의존한다. 터널이 끊기면 키워드 파서로 동작한다. 근본 대응은 GPU 서버다.
- ARM 운영 서버에서는 GPU 오버레이와 LoRA 해석을 쓰지 않는다.
- Celery 워커는 코드와 프로필(`phase2`)만 있고 기본 운영 경로가 아니다. 기본 배치는 API 프로세스 안에서 한 장씩 처리한다.
- 오픈 보캐브(Grounding DINO · SAM2)는 가중치가 없고 `OPEN_VOCAB_ENABLED=false`다. 없는 상태에서 켜면 동작하지 않는다.
- 움직이는 카메라의 영상 지우기는 일부 클립이 아직 예전 방식이다.
- 스키마 마이그레이션 도구(Alembic)가 없다.

추가하려는 것: GPU 추론 서버(LoRA · 오픈 보캐브) · 서버 밖 백업 · 필요해지면 문장만 보내는 클라우드 보조 해석 (사진을 보내지 않는 원칙은 유지).

---

## 관련 문서

- [`docs/plan/LOGIC_STRUCTURE.md`](../docs/plan/LOGIC_STRUCTURE.md) — 통합 로직 구조
- [`docs/plan/DATABASE.md`](../docs/plan/DATABASE.md) — DB 설계
- [`docs/guidance/llm-and-vision.md`](../docs/guidance/llm-and-vision.md) — 프롬프트 규격 · 모델 · RAG
- [`docs/guidance/auth.md`](../docs/guidance/auth.md) — 계정 · 메일
- [`docs/guidance/security.md`](../docs/guidance/security.md) — 보안 점검표
- [`docs/guidance/api-usage.md`](../docs/guidance/api-usage.md) — API 사용
- [`RUN.md`](../RUN.md) — 실행 가이드
