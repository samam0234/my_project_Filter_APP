# backend — FastAPI 백엔드

컷앤킵의 **API · 이미지 파이프라인 · DB** 를 담당한다.

## 역할

| 영역 | 경로 | 설명 |
|------|------|------|
| 진입점 | `app/main.py` | FastAPI 앱, CORS, lifespan, `/health` |
| 라우터 | `app/routers/` | upload, jobs, feedback, batch |
| 스키마 | `app/schemas/` | Pydantic 요청/응답 DTO |
| 서비스 | `app/services/` | OpenCV, 세그, 효과, 검증, 피드백 (아래 표) |
| 워크플로 | `app/workflows/` | LangGraph 노드·그래프 |
| 레포지토리 | `app/repositories/` | SQL 접근 |
| ORM | `app/models/` | jobs, feedbacks, batch_jobs |
| DB | `app/db/` | 엔진, 세션, `init_db` |
| 설정 | `app/core/` | config, security, constants |

### 서비스 모듈

| 파일 | 역할 |
|------|------|
| `prompt_spec.py` | 프롬프트 규격 정본 — LLM 지시문, LoRA 템플릿, `normalize_parsed` |
| `prompt_llm.py` | `LLM_PROVIDER` 분기 (ollama · openai · gemini · lora), 실패 시 `LLMError` |
| `prompt_lora.py` | LoRA 어댑터 로컬 추론 (transformers + peft, 싱글톤) |
| `segmentation.py` | YOLO-seg 인스턴스 · 대상 라벨 필터 · 라벨 별칭 · stub |
| `instance_selector.py` | 같은 클래스 중 위치·순서·개수·색 속성으로 인스턴스 선택 |
| `validator.py` | 마스크 품질 점수 → ok / fallback / failed |
| `effects.py` | GrabCut 정제, 배경 제거·블러·크롭, `remove_object` inpaint |
| `image_processor.py` | 전처리 (리사이즈 + CLAHE) |
| `feedback_service.py` | 피드백 DB + `data/feedback/` 사이드카 |

### 런타임 폴더 (backend/ 기준)

| 폴더 | 내용 |
|------|------|
| `data/` | `uploads/{job_id}/`, `cutnkeep.db` |
| `models/` | 서빙 가중치 `yolo26s-seg.pt`, LoRA 어댑터 `lora/` |
| `logs/` | `app_YYYY-MM-DD.log` |

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
