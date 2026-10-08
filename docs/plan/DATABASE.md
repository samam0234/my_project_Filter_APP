# 컷앤킵 (Cut & Keep) — 데이터베이스 설계

**한 줄 요약**
DB 가 둘이다. **서비스 DB (SQLite)** = 계정·작업 기록, **학습 DB (MariaDB)** = 피드백 이벤트·학습 데이터 카탈로그.
이미지·영상은 어느 DB 에도 넣지 않고 **파일 경로만** 기록한다. 접근은 Repository / 서비스 계층을 통한다.

| DB | 테이블 | 기본 엔진 | 엔진 코드 |
|----|--------|-----------|-----------|
| 서비스 DB | `users` · `auth_sessions` · `auth_codes` · `jobs` · `batch_jobs` | SQLite `backend/data/cutnkeep.db`(Docker) · `cutnkeep.host.db`(호스트) | `app/db/session.py` (`Base`) |
| 학습 DB | `feedbacks` · `learning_samples` | MariaDB (`MARIADB_*`) | `app/db/learning.py` (`LearningBase`) |

왜 나눴나: 서비스 데이터는 작고 요청마다 읽혀서 파일 하나짜리 SQLite 가 단순·빠르다.
학습 데이터 기록은 계속 쌓이고 검수·집계·외부 도구(DBeaver·학습 스크립트)에서 조회하므로 서버형 MariaDB 에 둔다.

**관련 코드**
- 연결: `backend/app/db/`
- ORM 테이블: `backend/app/models/`
- 저장소: `backend/app/repositories/`
- API DTO: `backend/app/schemas/`
- 라우터: `backend/app/routers/`

---

## 1. 계층 구조 (요청 흐름)

```
Router (HTTP)
   ↓ Depends(get_db)
Service / Workflow (비즈니스 · 이미지 파이프라인)
   ↓
Repository (SQL only)
   ↓
SQLAlchemy Engine
   ↓
SQLite (local)  |  MariaDB (prod / docker)
```

| 계층 | 경로 | 책임 |
|------|------|------|
| **Router** | `app/routers/` | 요청 검증, Depends, 응답 매핑 |
| **Schema** | `app/schemas/` | Pydantic 요청/응답 DTO |
| **Service / Workflow** | `app/services/`, `app/workflows/` | 처리 로직, 파일 I/O |
| **Repository** | `app/repositories/` | INSERT/SELECT/UPDATE, commit |
| **Model (ORM)** | `app/models/` | 테이블 정의 |
| **DB** | `app/db/` | engine, session, `init_db` |

**규칙**
- Router는 SQL을 직접 쓰지 않는다 → Repository만 호출
- Repository는 OpenCV/LLM을 모른다
- ORM 모델(`models`)과 API 스키마(`schemas`)를 섞지 않는다

---

## 2. 엔진 선택

| DB | 기본 | 설정 | 직접 URL (최우선) |
|----|------|------|-------------------|
| 서비스 DB | SQLite | `DB_DIALECT=sqlite`, `SQLITE_PATH=data/cutnkeep.host.db` (호스트, backend/ 기준) · Docker 는 `data/cutnkeep.db` | `DATABASE_URL` |
| 학습 DB | MariaDB | `LEARNING_DB_DIALECT=mariadb` + `MARIADB_*` (또는 `sqlite` → `LEARNING_SQLITE_PATH`) | `LEARNING_DATABASE_URL` |

학습 DB 는 MariaDB 가 꺼져 있어도 서비스가 뜨도록 **로컬 SQLite fallback** 이 있다
(`LEARNING_DB_FALLBACK_SQLITE=true`, `backend/data/learning.db`, 경고 로그 · `/health` 의 `learning_db: "sqlite(fallback)"`).
MariaDB 를 다시 켜고 재기동하면 사이드카 파일에서 빠진 기록이 MariaDB 로 동기화된다.
MariaDB 접속을 기다리는 시간은 `LEARNING_DB_CONNECT_TIMEOUT`(기본 3초) — 꺼져 있을 때 기동이 오래 멈추지 않게 짧게 둔다.
Docker 에서는 MariaDB healthy 후에만 backend 가 뜨므로 fallback 을 끈다.

### 2.1 환경변수

```env
DB_DIALECT=sqlite          # 또는 mariadb
SQLITE_PATH=data/cutnkeep.host.db   # backend/ 기준 → backend/data/cutnkeep.host.db (Docker 는 compose 가 data/cutnkeep.db 로 덮음)

# --- 호스트 도구(DBeaver) / 로컬 클라이언트 기준 ---
MARIADB_HOST=localhost
MARIADB_PORT=3309          # 호스트 발행 포트 (.env). 컨테이너 내부는 항상 3306
MARIADB_USER=admin         # compose MYSQL_USER 와 동일 계열
MARIADB_PASSWORD=...       # 배포 시 교체. 변경 후 기존 데이터면 data/mariaDB_datas 삭제 후 재생성
MARIADB_DATABASE=cutnkeep
MYSQL_ROOT_PASSWORD=...    # 볼륨 최초 생성 시에만 적용

# 선택: 전체 URL이 있으면 dialect 헬퍼보다 우선
# DATABASE_URL=mysql+pymysql://admin:...@127.0.0.1:3309/cutnkeep?charset=utf8mb4

DB_ECHO=false
```

| 실행 위치 | 서비스 DB | 학습 DB (Host:Port) |
|-----------|-----------|---------------------|
| 로컬 uvicorn (기본) | sqlite | `127.0.0.1:MARIADB_PORT` (Docker MariaDB) — 꺼져 있으면 sqlite fallback |
| **backend 컨테이너** | sqlite (`./backend/data` 볼륨) | **`mariadb:3306`** (compose 가 강제) |

Docker MariaDB: 공식 `mariadb:11`, **비밀번호만**, `skip_ssl`. GSS 미사용.  
→ `docker/mariadb/README.md`, `docs/plan/CURRENT_STACK.md`

### 2.2 SQLAlchemy URL 예시

```text
# SQLite (로컬)
sqlite:///D:/…/my_project_Filter_APP/backend/data/cutnkeep.db

# MariaDB (호스트 → published port)
mysql+pymysql://admin:...@127.0.0.1:3309/cutnkeep?charset=utf8mb4

# MariaDB (backend 컨테이너 내부)
mysql+pymysql://admin:...@mariadb:3306/cutnkeep?charset=utf8mb4
```

코드: `Settings.database_url` (`app/core/config.py`)

### 2.3 기동 시 테이블 생성

학습 DB: `lifespan` → `init_learning_db()` (접속 확인 → fallback → `LearningBase.metadata.create_all()`)
→ `sync_from_files()` — `data/feedback/*.json`·`data/pseudo_labels/*.json` 중 DB 에 없는 것만 적재 (멱등, `LEARNING_SYNC_ON_START`)
→ `sync_requests_from_jobs()` — 서비스 DB `jobs` 의 요청 문장 중 아직 후보가 아닌 것 (`LEARNING_COLLECT_REQUESTS`).

서비스 DB: `lifespan` → `init_db()` → `Base.metadata.create_all()` → `_ensure_columns()`
`create_all` 은 **없는 테이블만** 만들고 기존 테이블에 컬럼을 추가하지 않는다.
그래서 `db/session.py` 의 `_ADDED_COLUMNS` 목록에 있는 컬럼만 `ALTER TABLE … ADD COLUMN … NULL` 로 보강한다
(현재 `jobs.user_id`, `batch_jobs.user_id`). 스키마 변경이 잦아지면 Alembic 도입 권장.

---

## 3. ERD (논리)

```
┌──────────────── users ───────────────┐
│ id (PK), username (UQ), email (UQ)   │
│ display_name, password_hash (scrypt) │
│ failed_logins, locked_until          │
│ last_login_at, created_at, updated_at│
└──────┬───────────────┬───────────────┘
       │ 1:N CASCADE   │ 1:N CASCADE          (jobs.user_id → SET NULL)
       ▼               ▼
 auth_sessions      auth_codes
 id=sha256(token)   purpose, code_hash(HMAC)
 expires_at         attempts, expires_at, used_at

┌──────────────── jobs ────────────────┐
│ id (PK), user_id (FK, NULL 허용)     │
│ kind (image | video | gif)           │
│ prompt, status, parsed_prompt(JSON)  │
│ quality_score, before_path, after_path│
│ backend, labels, confidences, message│
│ feedback_saved, error                │
│ created_at, updated_at, expires_at   │
└──────────────────────────────────────┘
        ┆ job_id · user_id 를 값으로만 참조 (DB 가 달라 FK 없음)
════════╪═══════════════ 학습 DB (MariaDB) ═══════════════
        ▼
┌──────────── feedbacks ───────────────┐      ┌────────── learning_samples ──────────┐
│ id (PK) = case_id = 사이드카 파일명  │ 1:N  │ id (PK), origin_id (+kind 유일)       │
│ job_id, user_id                      │─────▶│ kind: prompt | segment                │
│ vote, comment, source, prompt        │      │ source: correction | like | request | │
│ image_path (경로), meta(JSON)        │      │   pipeline_failure | pseudo_label     │
│ created_at                           │      │ status: pending|approved|rejected|del │
└──────────────────────────────────────┘      │ split: train | val                    │
                                              │ prompt, answer(JSON 정답)             │
                                              │ image_path, label_path (경로)         │
                                              │ note, reviewed_by, reviewed_at        │
                                              └───────────────────────────────────────┘
════════════════════════════════════════════════════════════

┌────────── batch_jobs (Phase 2) ──────┐
│ id, status, prompt                   │
│ total, completed, progress           │
│ message, item_results(JSON)          │
│ created_at, updated_at               │
└──────────────────────────────────────┘
```

### 3.1 테이블 상세

#### `users` · `auth_sessions` · `auth_codes`
계정 기능 — 상세 규칙·보안은 [`docs/guidance/auth.md`](../guidance/auth.md)

| 테이블 | 핵심 컬럼 | 비고 |
|--------|-----------|------|
| `users` | username · email (소문자, 유일) · password_hash · failed_logins · locked_until | 비밀번호 원문 저장 없음 |
| `auth_sessions` | id = 세션 토큰 SHA-256 · user_id · expires_at | 토큰 원문은 쿠키에만 |
| `auth_codes` | user_id · purpose · code_hash · attempts · expires_at · used_at | 재설정 코드, 1회용 |

#### `jobs`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | str(64) PK | job UUID |
| user_id | str(32) NULL | 로그인 상태로 처리한 작업의 소유자 (비로그인 NULL) |
| kind | str(16) NULL | **image**(사진) · **video**(영상) · **gif** — NULL 인 예전 행은 image. 기동 시 `ALTER TABLE` 로 추가됨 |
| prompt | text | 사용자 프롬프트 |
| status | str | pending / ok / fallback / failed (영상·GIF 는 ok) |
| parsed_prompt | JSON | 구조화 프롬프트 |
| quality_score | float | 검증 점수 |
| before_path / after_path | str | 디스크 경로 — 사진 `uploads/{id}/before.jpg · after.png|jpg`, GIF `uploads/{id}/before.gif · after.gif`(+ `after.webp`), 영상 `uploads/videos/{id}/in.* · result.mp4`(+ `thumb.jpg`, avi 등은 `original.mp4` 미리 보기) |
| backend | str | yolo / stub 등 |
| labels / confidences | JSON | 세그 결과 메타 |
| feedback_saved | int 0/1 | 피드백 존재 여부 |
| expires_at | datetime | 업로드 파일 만료 (기본 24h) |

#### `feedbacks` (학습 DB)
사용자·파이프라인 피드백 **이벤트** 원장. 원본은 `data/feedback/{id}.json` 사이드카.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | str(64) PK | case id (= 사이드카 파일명) |
| job_id · user_id | str | 서비스 DB 값 참조 (FK 없음) |
| vote | str | like / dislike |
| comment | text | dislike 코멘트 — 정답 JSON 이면 교정 |
| source | str | user / pipeline_failure |
| prompt | text | 요청 문장 (job 에서 보강) |
| image_path | str | 저장소 루트 기준 상대 경로 (실패 원본 이미지) |
| meta | JSON | parsed_prompt, scores 등 |

#### `learning_samples` (학습 DB)
**학습에 쓸 수 있는 데이터 목록** (카탈로그). 피드백 1건에서 0~2개 파생, 의사 라벨 1건에서 1개.

| 컬럼 | 설명 |
|------|------|
| kind | `prompt` (문장 → ParsedPrompt 정답, LoRA·RAG) / `segment` (세그 실패 이미지, YOLO 재학습 후보) |
| source | `correction` (정답 알려주기) · `like` · `request` (회원 요청 + 시스템 해석) · `pipeline_failure` · `pseudo_label` |
| status | `pending` → 운영 콘솔에서 `approved` / `rejected`. 삭제하면 `deleted` (내용·경로를 비운 표식, 재동기화 방지) |
| split | 승인 시 id 해시로 `train` / `val` 고정 (10% val) |
| prompt · answer | 문장 · 정답 JSON |
| image_path · label_path | 이미지 · 사이드카 JSON 의 저장소 루트 기준 상대 경로 (Docker·호스트 공통) |
| origin_id | 출처 레코드 id — (origin_id, kind) 유일이라 같은 출처를 두 번 넣지 않음 |

#### `batch_jobs` (Phase 2)
배치 작업 진행률·상태 저장. 현재 API는 stub + DB row 생성. `user_id` = 등록한 회원 (배치는 회원 전용).

---

## 4. 저장 정책

비로그인 업로드는 **아무것도 저장하지 않는다** (jobs 행·업로드 파일·실패 사이드카 모두 없음 — 결과는 응답의 data URL 로만).
아래는 로그인 회원 작업 기준.

| 데이터 | DB | 디스크 |
|--------|----|--------|
| Job 메타 (status, prompt, paths) | ✅ `jobs` | — |
| Before/After 이미지 | 경로만 DB | `backend/data/uploads/{job_id}/` |
| 피드백 이벤트 | ✅ 학습 DB `feedbacks` | 원본 JSON 사이드카 `data/feedback/` |
| 학습 데이터 목록 (정답·검수 상태) | ✅ 학습 DB `learning_samples` | — |
| 실패 이미지 | 경로만 (학습 DB) | `data/feedback/*.jpg` |
| 배치 진행률 | ✅ `batch_jobs` | — |

일반 업로드 파일은 **영구 저장하지 않음** (`FILE_RETENTION_HOURS`, 기본 24h).  
피드백 실패 케이스는 학습 루프용으로 별도 보관.

---

## 5. Repository API (요약)

| 클래스 | 주요 메서드 |
|--------|-------------|
| `JobRepository` | `get`, `create_pending`, `save_result`, `mark_feedback_saved`, `list_recent` |
| `FeedbackRepository` (학습 DB) | `list_by_job`, `get` — 저장은 `learning_catalog.record_feedback` |
| `BatchRepository` | `create`, `get`, `update_progress` |
| `UserRepository` | `by_username`, `by_email`, `create`, 세션 `add/get/delete`, 코드 `replace/active/latest` |

업로드 라우터 흐름:
1. `run_pipeline(...)`  
2. `JobRepository.save_result(result, prompt, user_id)` — 로그인 상태면 소유자 연결    

피드백 라우터 흐름 (`FeedbackService.save_case`) — 두 DB 사이 트랜잭션이 없어 원본 파일을 먼저 남긴다:
1. 서비스 DB `jobs` 에서 prompt·parsed_prompt·user_id 보강
2. 파일 사이드카 `data/feedback/{case_id}.json` (+ 실패 이미지 `.jpg`)
3. 학습 DB `feedbacks` + 파생 `learning_samples` (`learning_catalog.record_feedback`) — 실패해도 다음 기동 때 사이드카에서 복구
4. 서비스 DB `JobRepository.mark_feedback_saved(job_id)`

---

## 6. 로컬 / Docker 사용법

### 로컬 (SQLite — 기본)

```bash
# .env
DB_DIALECT=sqlite
SQLITE_PATH=data/cutnkeep.host.db   # backend/ 기준 (Docker 와 다른 파일)

# 루트에서 venv 활성화 후
cd backend
uvicorn app.main:app --reload
# → backend/data/cutnkeep.host.db 자동 생성 + 테이블 create
```

학습 DB 는 Docker MariaDB 를 쓴다 (`docker compose -p cut_and_keep up -d mariadb`).
꺼 두면 `backend/data/learning.db` 로 대체되고, 켜고 재기동하면 MariaDB 로 동기화된다.

### Docker

```bash
docker compose -p cut_and_keep --env-file .env up -d --build
# backend environment: DB_DIALECT=sqlite, SQLITE_PATH=${DOCKER_SQLITE_PATH:-data/cutnkeep.db}, LEARNING_DB_DIALECT=mariadb, MARIADB_HOST=mariadb
```

### 호스트와 Docker 는 다른 SQLite 파일을 쓴다

`backend/data` 가 Docker 에 bind mount 되어 있어, 같은 `SQLITE_PATH` 를 쓰면 호스트 backend 와 Docker backend 가 **한 파일을 번갈아 쓴다**.
2026-10-08 이 상태에서 `jobs` 루트 페이지가 다른 프로세스의 로그 텍스트(OpenCV 경고)로 덮여 DB 가 깨졌고 업로드가 모두 500 이 됐다.
그래서 호스트 기본은 `cutnkeep.host.db`, Docker 는 `cutnkeep.db` 로 나눴다. 두 값을 같게 맞추지 않는다.

### 자동 백업

서비스 DB 가 SQLite 면 백엔드가 기동 직후 + `DB_BACKUP_HOURS`(기본 24)마다 `backend/data/backups/{파일명}-YYYYmmdd-HHMMSS.db` 로
SQLite 온라인 백업을 만들고 최근 `DB_BACKUP_KEEP`(기본 7)개만 남긴다 (`app/services/db_backup.py`).
백업본도 `quick_check` 로 확인해 원본이 이미 깨졌으면 그 백업은 버린다 — 좋은 백업이 밀려나지 않게.
아래 복구 절차에서 **가장 최근 백업을 `cutnkeep.db` 로 두는 것**이 첫 번째 방법이다.

### 손상 복구

기동 시 `PRAGMA quick_check` 결과가 `ok` 가 아니면 `서비스 DB 손상 감지` 오류 로그가 남는다 (`app/db/session.py:check_sqlite_integrity`).

1. backend(와 worker) 컨테이너를 멈춘다 — `docker stop cut_and_keep-backend-1`
   - 백업이 있으면: 원본을 이름 바꿔 보존하고 `backend/data/backups/` 의 가장 최근 파일을 `cutnkeep.db` 로 복사한 뒤 4번으로
2. 원본을 지우지 말고 이름을 바꿔 보존한다 — 예: `cutnkeep.corrupt-YYYYMMDD.db` (`*.db` 라 git 에 안 들어간다)
3. 복사본에서 읽히는 테이블(`users` · `auth_sessions` 등)을 같은 스키마(`sqlite_master.sql`)로 만든 새 파일에 옮긴다. 읽히지 않는 `jobs` 는 보존 기한이 지나면 의미가 없으므로 버려도 된다
4. 새 파일을 `cutnkeep.db` 로 두고 backend 를 다시 띄운 뒤 업로드 한 번으로 확인한다

### 분리 이전 데이터

분리 전 서비스 DB 에 있던 `feedbacks` 테이블은 지우지 않고 남겨 둔다 (더 이상 쓰지 않음).
같은 내용의 원본 사이드카가 `data/feedback/` 에 있어 기동 시 학습 DB 로 자동 적재된다.

`docker-compose.yml`에 `mariadb` 서비스 + healthcheck 포함.

---

## 7. 의존성

```txt
SQLAlchemy==2.0.35
PyMySQL==1.1.1
cryptography==43.0.1
```

SQLite는 Python 표준 라이브러리 드라이버 사용 (추가 패키지 불필요).

---

## 8. 향후 (선택)

- Alembic 마이그레이션 (`alembic revision --autogenerate`)
- Job/Feedback 비동기 세션 (`asyncmy` / `aiosqlite`)
- 배치 결과 정규화 테이블 (item 단위)

---

**다음 액션**  
1. 로컬에서 SQLite로 **로그인 후** `/api/v1/upload` → `/api/v1/jobs/{id}` 조회 확인 (비로그인 업로드는 저장되지 않음)  
2. Docker Compose로 MariaDB 연동 스모크 테스트  
