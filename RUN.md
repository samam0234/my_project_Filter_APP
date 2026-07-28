# 컷앤킵 — 실행 · 서버 열기 가이드

로컬에서 백엔드 / 사용자 앱 / 운영 콘솔을 띄우는 방법과  
Docker(`cut_and_keep`) 스택 실행 방법을 정리한다.

더 자세한 문서: `docs/guidance/getting-started.md`, `docs/guidance/docker-run.md`

---

## 1. 사전 준비

| 항목 | 권장 |
|------|------|
| Python | 3.10 ~ 3.12 (**3.11 권장**, 3.14 비권장) |
| Node.js | 18.x 또는 20.x LTS |
| Docker Desktop | 선택 (전체 스택) |
| Git | 2.30+ |
| **Ollama** (로컬 LLM) | `gemma4:e4b` — 프롬프트 분석 기본 |
| **yolo26s-seg** 가중치 | `models/yolo26s-seg.pt` 또는 `.onnx` |

AI 모델 전략: [`docs/plan/AI_MODEL_STRATEGY.md`](./docs/plan/AI_MODEL_STRATEGY.md)  
LLM 실행: [`docs/guidance/llm-and-vision.md`](./docs/guidance/llm-and-vision.md)

### Ollama (로컬 LLM) 빠른 설정

```powershell
ollama pull gemma4:e4b
ollama serve
# .env: LLM_PROVIDER=ollama , OLLAMA_MODEL=gemma4:e4b
```

### 환경변수

```powershell
# 저장소 루트 (CutNKeep)
cd d:\my_project\CutNKeep
copy .env.example .env
# 필요 시 .env 수정 (OPENAI_API_KEY, DB 등)
```

로컬 기본 DB: `DB_DIALECT=sqlite` → `data/cutnkeep.db`

---

## 2. 포트 한눈에

| 서비스 | 포트 | URL |
|--------|------|-----|
| Backend (FastAPI) | **8000** | http://localhost:8000 |
| API Swagger | 8000 | http://localhost:8000/docs |
| Health | 8000 | http://localhost:8000/health |
| Frontend (사용자) | **5173** | http://localhost:5173 |
| Console (운영) | **5174** | http://localhost:5174 |
| MariaDB (Docker **호스트**) | **`.env` `MARIADB_PORT`** (예 **3309**) | DBeaver: `127.0.0.1` |
| Redis (Docker 호스트) | **6380** | — |
| Adminer (Docker) | **8081** | http://localhost:8081 · Server=`mariadb` |
| Frontend (Docker nginx) | 80 | http://localhost |

현재 스택 한장 요약: [`docs/plan/CURRENT_STACK.md`](./docs/plan/CURRENT_STACK.md)

---

## 3. 로컬 실행 (개발 권장)

터미널을 **3개** 쓰는 것을 권장한다.

### 3.1 Backend

Python 의존성 파일은 **저장소 루트**에 있다 (`requirements.txt`, `requirements.docker.txt`).

```powershell
cd d:\my_project\CutNKeep
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# 가벼운 Docker와 비슷하게: pip install -r requirements.docker.txt

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

확인:

```powershell
curl http://localhost:8000/health
# 또는 브라우저: http://localhost:8000/docs
```

### 3.2 Frontend (사용자 앱)

```powershell
cd d:\my_project\CutNKeep\frontend
npm install
npm run dev
```

→ http://localhost:5173  
Vite가 `/api`, `/health` 를 `8000` 으로 프록시한다.

### 3.3 Console (운영 관리자)

```powershell
cd d:\my_project\CutNKeep\console
# 최초 1회 필수 — node_modules 없으면 vite 실행 불가
npm install
npm run dev
```

→ http://localhost:5174  
Job 목록·헬스 조회. **백엔드가 떠 있어야** 데이터가 채워진다.  
(UI 기동만은 backend 없이도 가능)

---

## 4. Docker 로 한 번에 (`cut_and_keep`)

```powershell
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초 1회 — MARIADB_PORT·계정 확인
docker compose -p cut_and_keep --env-file .env up -d --build
docker compose -p cut_and_keep ps
```

| 컨테이너 | 포트 |
|----------|------|
| backend | http://localhost:8000 |
| frontend | http://localhost (80) |
| mariadb | localhost:**MARIADB_PORT** (예 3309) → 3306 |
| redis | localhost:6380 → 6379 |
| adminer | http://localhost:8081 |

로그:

```powershell
docker compose -p cut_and_keep logs -f backend
```

중지:

```powershell
docker compose -p cut_and_keep down          # 볼륨 유지
docker compose -p cut_and_keep down -v       # DB 계정/데이터 초기화
```

### 참고

- Docker 백엔드는 **MariaDB** (`DB_DIALECT=mariadb`, 호스트 DNS `mariadb:3306`).
- MariaDB는 **비밀번호 로그인만** (GSS/SSL 미사용). 상세: `docker/mariadb/README.md`
- 백엔드 이미지는 루트 `requirements.docker.txt` (경량, YOLO/torch 없음 → stub 세그 가능). 빌드 context = 저장소 루트.
- **Console 은 Compose에 없음** → 로컬 `npm run dev` (5174).
- Redis 호스트 포트 **6380** (6379 충돌 회피).
- 구 스택 이름 `cutnkeep` 과 동시 기동 금지.

상세: `docs/plan/CURRENT_STACK.md`, `docs/guidance/docker-run.md`, `docs/repeater/`

---

## 5. 기동 전 테스트 (권장)

```powershell
cd d:\my_project\CutNKeep
pip install -r tests/requirements-test.txt
# backend 의존성 설치 후:
pytest
# 의존성 없을 때 골격만:
pytest tests/structure -q
```

상세: `docs/plan/TESTING.md`, `tests/README.md`

## 6. 기동 순서 권장

1. (선택) `pytest`  
2. Backend (또는 Docker 스택)  
3. Frontend / Console  
4. 브라우저에서 health → 업로드 또는 Job 목록 확인  

---

## 7. 자주 막히는 것

| 증상 | 확인 |
|------|------|
| Frontend API 실패 | backend 8000 기동 여부 |
| Console offline | 동일 + CORS / 프록시 |
| Docker Redis 기동 실패 | 6379 충돌 → 6380 사용 |
| Docker backend Restarting | `docker compose -p cut_and_keep logs backend` · MariaDB healthy 여부 |
| DBeaver GSS / Access denied | 비밀번호 로그인, Host=`127.0.0.1`, Port=`MARIADB_PORT`, SSL/GSS 끔 |
| pip / pydantic 빌드 실패 | Python 3.11~3.12 venv 사용 (3.14 비권장) |

---

## 8. 관련 문서

| 문서 | 내용 |
|------|------|
| [README.md](./README.md) | 프로젝트 개요 |
| [docs/guidance/getting-started.md](./docs/guidance/getting-started.md) | 빠른 시작 |
| [docs/guidance/docker-run.md](./docs/guidance/docker-run.md) | Docker |
| [docs/guidance/console-admin.md](./docs/guidance/console-admin.md) | 운영 콘솔 |
| [Scribble/README.md](./Scribble/README.md) | 개인 메모 폴더 (git 제외) |
