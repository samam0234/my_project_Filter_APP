# backend — FastAPI 백엔드

컷앤킵의 **API · 이미지 파이프라인 · DB** 를 담당한다.

## 역할

| 영역 | 경로 | 설명 |
|------|------|------|
| 진입점 | `app/main.py` | FastAPI 앱, CORS, lifespan, `/health` |
| 라우터 | `app/routers/` | upload, jobs, feedback, batch |
| 스키마 | `app/schemas/` | Pydantic 요청/응답 DTO |
| 서비스 | `app/services/` | OpenCV, 세그, 효과, 검증, 피드백 |
| 워크플로 | `app/workflows/` | LangGraph 노드·그래프 |
| 레포지토리 | `app/repositories/` | SQL 접근 |
| ORM | `app/models/` | jobs, feedbacks, batch_jobs |
| DB | `app/db/` | 엔진, 세션, `init_db` |
| 설정 | `app/core/` | config, security, constants |

## 실행

Python 의존성은 **저장소 루트**에 둔다 (서버 전체가 Python 기준).

```powershell
# 저장소 루트에서
cd d:\my_project\CutNKeep
# Python 3.11 권장 (3.14 비권장)
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Docker 와 비슷한 경량: pip install -r requirements.docker.txt

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 문서: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

환경변수: 루트 `.env` / `.env.example`  
모델·LLM 전략: `docs/plan/AI_MODEL_STRATEGY.md`

## 의존성 파일 (루트)

| 파일 | 용도 |
|------|------|
| `../requirements.txt` | 로컬 개발 (YOLO/ultralytics 포함 가능) |
| `../requirements.docker.txt` | Docker 경량 런타임 |
| `Dockerfile` | 컨테이너 이미지 (빌드 context = 저장소 루트) |

## 테스트

```powershell
# 저장소 루트에서
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
pytest tests/unit tests/smoke
```

전체 전략: `docs/plan/TESTING.md`

## 관련 문서

- `docs/plan/LOGIC_STRUCTURE.md`
- `docs/plan/DATABASE.md`
- `docs/guidance/api-usage.md`
- `RUN.md` (루트 실행 가이드)
