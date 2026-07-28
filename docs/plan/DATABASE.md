# 컷앤킵 (Cut & Keep) — 데이터베이스 설계

**한 줄 요약**  
로컬은 **SQLite**, 배포/Docker는 **MariaDB**. 접근은 항상 **Repository** 계층을 통한다.

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

| 환경 | Dialect | 설정 |
|------|---------|------|
| **로컬 개발 (기본)** | SQLite | `DB_DIALECT=sqlite`, `SQLITE_PATH=data/cutnkeep.db` |
| **Docker / 스테이징 / 운영** | MariaDB | `DB_DIALECT=mariadb` + `MARIADB_*` |
| **직접 URL** | 아무거나 | `DATABASE_URL=...` (최우선) |

### 2.1 환경변수

```env
DB_DIALECT=sqlite          # 또는 mariadb
SQLITE_PATH=data/cutnkeep.db

# --- 호스트 도구(DBeaver) / 로컬 클라이언트 기준 ---
MARIADB_HOST=localhost
MARIADB_PORT=3309          # 호스트 발행 포트 (.env). 컨테이너 내부는 항상 3306
MARIADB_USER=admin         # compose MYSQL_USER 와 동일 계열
MARIADB_PASSWORD=...       # 배포 시 교체. 변경 후 기존 볼륨이면 down -v
MARIADB_DATABASE=cutnkeep
MYSQL_ROOT_PASSWORD=...    # 볼륨 최초 생성 시에만 적용

# 선택: 전체 URL이 있으면 dialect 헬퍼보다 우선
# DATABASE_URL=mysql+pymysql://admin:...@127.0.0.1:3309/cutnkeep?charset=utf8mb4

DB_ECHO=false
```

| 실행 위치 | Host | Port | Dialect |
|-----------|------|------|---------|
| 로컬 uvicorn (기본) | — | — | **sqlite** |
| 호스트 → Docker MariaDB | `127.0.0.1` | `MARIADB_PORT` | mariadb |
| **backend 컨테이너** | **`mariadb`** | **`3306`** | compose 가 강제 |

Docker MariaDB: 공식 `mariadb:11`, **비밀번호만**, `skip_ssl`. GSS 미사용.  
→ `docker/mariadb/README.md`, `docs/plan/CURRENT_STACK.md`

### 2.2 SQLAlchemy URL 예시

```text
# SQLite (로컬)
sqlite:///D:/my_project/CutNKeep/data/cutnkeep.db

# MariaDB (호스트 → published port)
mysql+pymysql://admin:...@127.0.0.1:3309/cutnkeep?charset=utf8mb4

# MariaDB (backend 컨테이너 내부)
mysql+pymysql://admin:...@mariadb:3306/cutnkeep?charset=utf8mb4
```

코드: `Settings.database_url` (`app/core/config.py`)

### 2.3 기동 시 테이블 생성

`lifespan` → `init_db()` → `Base.metadata.create_all()`  
Phase 1 스캐폴드용. 이후 스키마 변경이 잦아지면 Alembic 도입 권장.

---

## 3. ERD (논리)

```
┌──────────────── jobs ────────────────┐
│ id (PK)                              │
│ prompt, status, parsed_prompt(JSON)  │
│ quality_score, before_path, after_path│
│ backend, labels, confidences, message│
│ feedback_saved, error                │
│ created_at, updated_at, expires_at   │
└──────────────────┬───────────────────┘
                   │ 1:N
                   ▼
┌──────────── feedbacks ───────────────┐
│ id (PK)                              │
│ job_id (FK → jobs.id) CASCADE        │
│ vote, comment, source                │
│ image_path, meta(JSON)               │
│ created_at                           │
└──────────────────────────────────────┘

┌────────── batch_jobs (Phase 2) ──────┐
│ id, status, prompt                   │
│ total, completed, progress           │
│ message, item_results(JSON)          │
│ created_at, updated_at               │
└──────────────────────────────────────┘
```

### 3.1 테이블 상세

#### `jobs`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | str(64) PK | job UUID |
| prompt | text | 사용자 프롬프트 |
| status | str | pending / ok / fallback / failed |
| parsed_prompt | JSON | 구조화 프롬프트 |
| quality_score | float | 검증 점수 |
| before_path / after_path | str | 디스크 경로 |
| backend | str | yolo / stub 등 |
| labels / confidences | JSON | 세그 결과 메타 |
| feedback_saved | int 0/1 | 피드백 존재 여부 |
| expires_at | datetime | 업로드 파일 만료 (기본 24h) |

#### `feedbacks`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | str(64) PK | case id |
| job_id | FK | 부모 job |
| vote | str | like / dislike |
| source | str | user / pipeline_failure |
| image_path | str | 사이드카 이미지 경로 (옵션) |
| meta | JSON | prompt, scores 등 |

#### `batch_jobs` (Phase 2)
배치 작업 진행률·상태 저장. 현재 API는 stub + DB row 생성.

---

## 4. 저장 정책

| 데이터 | DB | 디스크 |
|--------|----|--------|
| Job 메타 (status, prompt, paths) | ✅ `jobs` | — |
| Before/After 이미지 | 경로만 DB | `data/uploads/{job_id}/` |
| 피드백 메타 | ✅ `feedbacks` | 학습용 JSON 사이드카 `data/feedback/` |
| 실패 이미지 | 경로 가능 | `data/feedback/*.jpg` |
| 배치 진행률 | ✅ `batch_jobs` | — |

일반 업로드 파일은 **영구 저장하지 않음** (`FILE_RETENTION_HOURS`, 기본 24h).  
피드백 실패 케이스는 학습 루프용으로 별도 보관.

---

## 5. Repository API (요약)

| 클래스 | 주요 메서드 |
|--------|-------------|
| `JobRepository` | `get`, `create_pending`, `save_result`, `mark_feedback_saved`, `list_recent` |
| `FeedbackRepository` | `create`, `list_by_job`, `get` |
| `BatchRepository` | `create`, `get`, `update_progress` |

업로드 라우터 흐름:
1. `run_pipeline(...)`  
2. `JobRepository.save_result(result, prompt)`  

피드백 라우터 흐름:
1. (옵션) 파일 사이드카 저장  
2. `FeedbackRepository.create(...)`  
3. `JobRepository.mark_feedback_saved(job_id)`

---

## 6. 로컬 / Docker 사용법

### 로컬 (SQLite — 기본)

```bash
# .env
DB_DIALECT=sqlite
SQLITE_PATH=data/cutnkeep.db

# 루트에서 venv 활성화 후
cd backend
uvicorn app.main:app --reload
# → data/cutnkeep.db 자동 생성 + 테이블 create
```

### Docker (MariaDB)

```bash
docker compose up --build
# backend environment: DB_DIALECT=mariadb, MARIADB_HOST=mariadb
```

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
1. 로컬에서 SQLite로 `/api/v1/upload` 후 `/api/v1/jobs/{id}` 조회 확인  
2. Docker Compose로 MariaDB 연동 스모크 테스트  
