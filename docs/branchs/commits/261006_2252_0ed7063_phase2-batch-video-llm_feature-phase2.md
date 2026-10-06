# 배치·영상·오픈보캐브와 LLM 폴백 / `0ed706359f076ffc698be6db7517fdc330abe25c`

> 브랜치: `feature/phase2`  
> 작성일: `2026-10-06 22:52`  
> 작성자: `agent`  
> 파일명: `261006_2252_0ed7063_phase2-batch-video-llm_feature-phase2.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(phase2): 배치·영상·오픈보캐브와 LLM 폴백을 넣다` |
| **커밋 번호 (SHA)** | `0ed706359f076ffc698be6db7517fdc330abe25c` |
| **짧은 SHA** | `0ed7063` |
| **브랜치** | `feature/phase2` |
| **부모 커밋** | `0107f1bac633761a57d00363126c48c0eafb147d` |

## 2. 주 커밋 내용

- `LLM_FALLBACK`(기본 ollama). 기본 provider 가 `LLMError` 이면 한 번 더 시도하고, 성공한 이름을 `prompt_parser` 에 남긴다
- 회원 배치는 파일을 저장하고 `queued` 로 남긴 뒤 한 장씩 처리·진행률 갱신. `BATCH_USE_CELERY` 기본 false
- Celery 워커는 `docker compose --profile phase2` 의 `celery_worker` 만. 기본 `up` 에는 없다
- `OPEN_VOCAB_ENABLED` 일 때 클래스 밖 대상만 로컬 Grounding DINO+SAM2. 가중치·패키지가 없으면 YOLO/ONNX/stub
- `POST /api/v1/video`. 검출이 없는 프레임은 직전 마스크 유지. 비로그인은 저장하지 않는다

## 3. 상세 내용

### 3.1 배경 / 목적

남은 작업이던 Phase 2 스텁(배치, Celery, SAM2, 클라우드 LLM 폴백, 영상)을 기본 업로드 경로를 바꾸지 않는 범위에서 동작하게 만든다.

### 3.2 변경 범위

- 추가: `backend/app/routers/video.py`, `backend/app/services/video_processor.py`, `tests/unit/test_phase2.py`
- 수정: `prompt_llm.py`, `nodes.py`, `batch.py`, `batch_tasks.py`, `segmentation.py`, `config.py`, `router.py`, `docker-compose.yml`, `requirements.txt`, `requirements.docker.txt`, `.env.example`, 계획·API 문서, `tests/unit/test_prompt_llm.py`

### 3.3 기술 포인트

- 폴백은 같은 provider·heuristic·빈 값을 건너뛴다. 체인이 모두 실패하면 기존처럼 `LLMError` 후 휴리스틱
- 배치는 `ImageProcessor.process_batch_generator` 로 한 장씩. 항목 실패가 나머지를 멈추지 않는다
- 오픈보캐브는 `local_files_only`. 요청 중에 허브에서 받지 않는다
- 영상 출력은 MJPG avi. 배경제거 알파는 검은 배경 BGR 로 맞춘다
- 서빙 기본 비전은 그대로 YOLO26m-seg. 학습 출발 가중치 s-seg 도 그대로

### 3.4 의도적으로 하지 않은 것

- `prompt_spec.py` 변경과 LoRA 재학습. 학습 템플릿은 `LORA_TEMPLATE` 와 동일 객체
- 광학 흐름·LSTM, SAM2 가중치 다운로드, main 병합, 푸시, 배포
- 기본 compose 에 celery 워커를 올리는 것
- `PHASE` 상수는 1 유지 (`tests/smoke/test_imports.py`)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 로컬 실행 확인
- [x] Docker 확인
- [ ] API/UI 스모크 (브라우저 업로드는 이번 확인에 없음)
- 결과 서술:
  - `training/.venv` Python 3.12 로 pytest 전체 종료 코드 0. 셸의 `DEBUG=WARN` 은 설정 파싱을 깨서 그 변수만 지우고 돌렸다
  - frontend vitest 16 passed, console vitest 4 passed
  - `SEG_RUNTIME=onnx` 이미지 `cut_and_keep_onnx_smoke:local`. torch·ultralytics 없음, onnxruntime 1.19.2. `yolo26m-seg.onnx` 추론 `backend=onnx`
  - compose 스택은 올리지 않았다. 스모크 컨테이너는 `--rm`

### 4.2 부작용 / 리스크

- 기본 `LLM_FALLBACK=ollama` 라 클라우드·LoRA 실패 시 로컬 Ollama 가 떠 있으면 그 결과로 성공한다
- 오픈보캐브·Celery 는 플래그 기본값 false. 가중치나 워커 없이는 기존 경로
- 영상은 avi. mp4 코덱은 쓰지 않는다
- Docker 슬림 이미지에 celery·redis 패키지가 포함된다. 기본 기동은 워커를 띄우지 않는다

### 4.3 후속 작업

- develop 에 `feature/docs-sync`, `feature/phase2` 를 `--no-ff` 로 총 병합
- SAM2 가중치를 쓸 때는 로컬에 받은 뒤 `OPEN_VOCAB_ENABLED=true`
- main 병합·푸시·배포는 별도 지시 전까지 하지 않음

### 4.4 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/LOGIC_STRUCTURE.md`
- `docs/API_DOCUMENTATION.md`
- `docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`
