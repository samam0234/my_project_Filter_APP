# backend — FastAPI 백엔드

컷앤킵의 **API · 이미지 파이프라인 · DB** 를 담당한다.

## 역할

| 영역 | 경로 | 설명 |
|------|------|------|
| 진입점 | `app/main.py` | FastAPI 앱, CORS, lifespan, `/health` |
| 라우터 | `app/routers/` | upload(사진 · 파일), gif, video, jobs, feedback, batch, auth, console |
| 스키마 | `app/schemas/` | Pydantic 요청/응답 DTO |
| 서비스 | `app/services/` | OpenCV, 세그, 효과, 검증, 피드백 (아래 표) |
| 워크플로 | `app/workflows/` | LangGraph 노드·그래프 |
| 레포지토리 | `app/repositories/` | SQL 접근 |
| ORM | `app/models/` | users, auth_*, jobs(kind=image·video·gif), batch_jobs · 학습 DB feedbacks, learning_samples |
| DB | `app/db/` | 엔진, 세션, `init_db` |
| 설정 | `app/core/` | config, security, constants |

### 서비스 모듈

| 파일 | 역할 |
|------|------|
| `prompt_spec.py` | 프롬프트 규격 정본 — LLM 지시문, LoRA 템플릿, `normalize_parsed` |
| `prompt_llm.py` | `LLM_PROVIDER` 분기 (ollama · openai · gemini · lora), 실패 시 `LLMError` |
| `prompt_lora.py` | LoRA 어댑터 로컬 추론 (transformers + peft, 싱글톤) |
| `prompt_chain.py` | 해석 체인(LangChain Core) — LLM 답과 키워드 파서가 다르면 다수결 (`PROMPT_CHAIN=langchain`) |
| `heuristic_targets.py` | 키워드 파서 — 어휘 + 역할 규칙(남길 것 · 뺄 것 · 지울 것), LLM 이 꺼져도 동작 |
| `prompt_rag.py` | 승인된 교정·좋아요 문장 중 비슷한 것을 LLM 예시로 |
| `segmentation.py` | YOLO-seg 인스턴스 · 대상 라벨 필터 · 라벨 별칭 · stub |
| `stuff_segmentation.py` | 배경 덩어리(건물 · 하늘 · 도로 등) SegFormer ONNX |
| `mask_exclusion.py` | 고른 인스턴스에서 다른 인스턴스 몫 덜어내기 · 위험 신호(`meta.leak`) |
| `instance_selector.py` | 같은 클래스 중 위치·순서·개수·색 속성으로 인스턴스 선택 |
| `validator.py` | 마스크 품질 점수 → ok / fallback / failed |
| `effects.py` | 경계 다듬기, 배경 제거·블러·크롭, `remove_object`(LaMa → 실패 시 Telea) |
| `inpaint.py` | 학습형 인페인팅 LaMa ONNX (`backend/models/lama_fp32.onnx`) |
| `video_processor.py` | 영상 프레임 처리(`FrameRenderer` — GIF 와 공용) · 광학 흐름 스무딩 · mp4 변환 · 원본 미리 보기 |
| `gif_processor.py` | 움직이는 GIF 읽기 · 처리 · 투명 GIF / WebP 쓰기 |
| `image_processor.py` | 전처리 (리사이즈 + CLAHE, CLAHE 기본 끔) |
| `retention.py` · `maintenance.py` · `db_backup.py` | 보관 기간 정리 · 주기 작업(자동 정리 · 서비스 DB 백업) |
| `learning_catalog.py` · `learning_review.py` | 학습 후보 수집 · 콘솔 검수 |
| `user_admin.py` · `system_status.py` | 콘솔 회원 관리 · 시스템 스냅샷 |
| `feedback_service.py` | 피드백 DB + `data/feedback/` 사이드카 |
| `auth_service.py` | 가입 · 로그인 잠금 · 세션 · 아이디 찾기 · 비밀번호 재설정 규칙 |
| `mailer.py` | SMTP 발송 (미설정 시 로그에만 기록) |

계정 보조: `core/passwords.py`(scrypt·토큰·코드), `core/deps.py`(`current_user`),
`repositories/user_repository.py`, `routers/auth.py` → [`docs/guidance/auth.md`](../docs/guidance/auth.md)

접근 정책: `core/access.py` — `owned_job`(본인 작업만, 아니면 404) · `require_console`(관리자 로그인 또는 서버 PC).
속도 제한: `core/ratelimit.py` — `client_ip()` 는 `TRUSTED_PROXIES` 에서 온 요청만 `X-Real-IP` 를 믿는다.
업로드 검증: `core/security.py` — 확장자 · MIME · 시그니처 · 해상도(압축 폭탄) 순.
비로그인 업로드는 `routers/upload.py` 가 저장 없이 data URL 로 응답, 운영 콘솔 전체 조회는 `routers/console.py`.

### 런타임 폴더 (backend/ 기준)

| 폴더 | 내용 |
|------|------|
| `data/` | `uploads/{job_id}/`, `cutnkeep.db` |
| `models/` | 서빙 가중치 `yolo26m-seg.pt`, LoRA 어댑터 `lora/` |
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
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000   # 다른 기기에서 열 때만 0.0.0.0
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
