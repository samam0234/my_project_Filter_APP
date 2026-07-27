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
| MariaDB (Docker) | 3306 | — |
| Redis (Docker 호스트) | 6380 | — |
| Frontend (Docker nginx) | 80 | http://localhost |

---

## 3. 로컬 실행 (개발 권장)

터미널을 **3개** 쓰는 것을 권장한다.

### 3.1 Backend

```powershell
cd d:\my_project\CutNKeep\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# 가벼운 Docker와 비슷하게: pip install -r requirements.docker.txt

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
npm install
npm run dev
```

→ http://localhost:5174  
Job 목록·헬스 조회. **백엔드가 떠 있어야** 데이터가 채워진다.

---

## 4. Docker 로 한 번에 (`cut_and_keep`)

```powershell
cd d:\my_project\CutNKeep
copy .env.example .env   # 최초 1회

docker compose -p cut_and_keep up --build -d
docker compose -p cut_and_keep ps
```

| 컨테이너 | 포트 |
|----------|------|
| backend | http://localhost:8000 |
| frontend | http://localhost (80) |
| mariadb | localhost:3306 |
| redis | localhost:6380 → 6379 |

로그:

```powershell
docker compose -p cut_and_keep logs -f backend
```

중지:

```powershell
docker compose -p cut_and_keep down
```

### 참고

- Docker 백엔드는 **MariaDB** 연결 (`DB_DIALECT=mariadb`).
- 백엔드 이미지는 `requirements.docker.txt` (경량, YOLO/torch 없음 → stub 세그 가능).
- **Console 은 Compose에 없음** → 로컬 `npm run dev` (5174) 사용.
- 호스트 **6379** 가 다른 스택에 점유되면 Redis 는 **6380** 사용 (이미 설정됨).

상세 트러블슈팅: `docs/repeater/`, `docs/web_management/ports-inventory.md`

---

## 5. 기동 순서 권장

1. Backend (또는 Docker 스택)  
2. Frontend / Console  
3. 브라우저에서 health → 업로드 또는 Job 목록 확인  

---

## 6. 자주 막히는 것

| 증상 | 확인 |
|------|------|
| Frontend API 실패 | backend 8000 기동 여부 |
| Console offline | 동일 + CORS / 프록시 |
| Docker Redis 기동 실패 | 6379 충돌 → 6380 사용 |
| Docker backend Restarting | `docker compose -p cut_and_keep logs backend` |
| pip / pydantic 빌드 실패 | Python 3.11 venv 사용 |

---

## 7. 관련 문서

| 문서 | 내용 |
|------|------|
| [README.md](./README.md) | 프로젝트 개요 |
| [docs/guidance/getting-started.md](./docs/guidance/getting-started.md) | 빠른 시작 |
| [docs/guidance/docker-run.md](./docs/guidance/docker-run.md) | Docker |
| [docs/guidance/console-admin.md](./docs/guidance/console-admin.md) | 운영 콘솔 |
| [Scribble/README.md](./Scribble/README.md) | 개인 메모 폴더 (git 제외) |
