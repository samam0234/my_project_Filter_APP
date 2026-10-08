# Docker Run (`cut_and_keep`)

현재 구성 요약: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

```powershell
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초 1회 — MARIADB_PORT, 계정, MYSQL_ROOT_PASSWORD 확인
docker compose -p cut_and_keep --env-file .env up -d --build
docker compose -p cut_and_keep ps
```

| 서비스 | URL / 포트 | 열린 곳 |
|--------|------------|---------|
| frontend (nginx) | http://localhost | **공개** (유일) |
| backend API | http://127.0.0.1:8000 (`BACKEND_PORT`) | 이 PC 만 |
| Swagger | http://127.0.0.1:8000/docs | 이 PC 만 |
| **Adminer** | http://127.0.0.1:8081 · Server=`mariadb` | 이 PC 만 |
| MariaDB (호스트) | `127.0.0.1` + `.env` **`MARIADB_PORT`** (예: 3309) | 이 PC 만 |
| Redis (호스트) | 127.0.0.1:**6380** | 이 PC 만 |

- 내부 포트는 `BIND_HOST`(기본 `127.0.0.1`)에만 열린다. 다른 기기에서 backend 등에 직접 붙어야 할 때만 `BIND_HOST=0.0.0.0`
- **호스트에서 `uvicorn --reload` 를 따로 띄워 8000 이 차 있으면** backend 컨테이너가 뜨지 않는다 → `BACKEND_PORT=8001 docker compose -p cut_and_keep --env-file .env up -d`
  (nginx 는 컨테이너끼리 8000 으로 연결하므로 http://localhost 는 그대로)
- Docker 서비스 DB 는 **MariaDB** (호스트 개발 서버는 SQLite `cutnkeep.host.db`). 처음 전환하면 옛 `cutnkeep.db` 의 회원·작업을 자동으로 옮긴다
- MariaDB 는 `mariadb-backup` 이 매일 `data/mariaDB_backups/` 로 덤프한다 (7일 보관) — 복구는 `docs/plan/DATABASE.md`
- 대상 지우기 LaMa 모델(`backend/models/lama_fp32.onnx`, 208MB)은 git 에 없다 — 없으면 Telea 로 동작 (`backend/models/README.md`, 경로는 `INPAINT_MODEL_PATH`, 엔진은 `INPAINT_ENGINE`)
- backend 는 기동 시 **서비스 DB 백업**(`backend/data/backups/`)과 **보관 기간 지난 업로드 정리**를 스스로 돌린다

## 인증 · DB

- MariaDB: **비밀번호만** (GSS/SSL 미사용)
- DBeaver: Host `127.0.0.1`, Port=`MARIADB_PORT`, SSL/GSS 끔, 드라이버 MariaDB 권장
- Docker backend 는 compose 가 `mariadb:3306` 으로 붙음 (`.env` 의 localhost 무시)

## 중지

```powershell
docker compose -p cut_and_keep down          # DB 데이터 유지 (data/mariaDB_datas)
```

DB 초기화: `down` 후 `data/mariaDB_datas` 폴더를 삭제하고 다시 `up`
(bind mount 라 `down -v` 로는 지워지지 않는다).

## 참고

- 콘솔(`console/`)은 Compose **미포함** → 로컬 `npm run dev` (:5174)
- 백엔드 이미지: 루트 `requirements.docker.txt` + Dockerfile 에서 **ultralytics + CPU 전용 torch** (약 2.8 GB)
  - 세그 가중치(`.env` 의 `YOLO_MODEL_PATH` — 기본 `backend/models/yolo26m-seg.pt`, `docs/plan/YOLO26M_DEFAULT.md`)가 있어야 실제 마스크 (없으면 stub). 기동 로그 `YOLO 세그멘터 준비` 로 확인
  - 슬림 빌드: `SEG_RUNTIME=onnx docker compose … up -d --build backend` + `.env` 의 `YOLO_MODEL_PATH=models/yolo26m-seg.onnx` →
    torch·ultralytics 없이 onnxruntime 만, 이미지 **1.11 GB** ([`ONNX_INFERENCE.md`](../plan/ONNX_INFERENCE.md))
  - LangGraph 포함 — 로컬과 같은 그래프 경로 (로그에 `langgraph 미설치` 경고가 없어야 정상)
  - 서비스 DB 는 SQLite(`./backend/data`), 학습 DB 는 MariaDB — `/health` 의 `db_dialect: sqlite`, `learning_db: mysql`

## 점검 결과 (2026-10-06, 재빌드 후 실제 요청)

| 항목 | 결과 |
|------|------|
| `/health` | `db_dialect=sqlite` · `learning_db=mysql` |
| 세그 | 이전: ultralytics 없어 **stub(가짜) 마스크** → 이후: YOLO CPU 추론 — s 97~135 ms, (같은 날 교체한) m 225~345 ms |
| 해석 | 컨테이너 → 호스트 Ollama(`host.docker.internal`) 정상, parser=ollama |
| 파이프라인 | 이전: langgraph 없어 선형 실행 → 이후: LangGraph |
| frontend(nginx :80) | 화면 200 · 새로고침 경로(`/history`) 200 · `/health`·`/api` 프록시 정상 |
| 설정 점검 | development 라 경고만 (SECRET_KEY·DEBUG·SESSION_COOKIE_SECURE·SMTP_HOST·CORS) — 배포 전 `.env` 교체 |
- 상세 MariaDB: `docker/mariadb/README.md`
