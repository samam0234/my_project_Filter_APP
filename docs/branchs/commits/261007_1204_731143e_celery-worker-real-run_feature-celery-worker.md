# Celery 워커 실가동 점검에서 찾은 세션 연결·Redis 장애 폴백·compose 플래그 수정 / `731143ef853d0497aef7fda18541f025faa36426`

> 브랜치: `feature/celery-worker`  
> 작성일: `2026-10-07 12:10`  
> 작성자: `agent`  
> 파일명: `261007_1204_731143e_celery-worker-real-run_feature-celery-worker.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(batch): Celery 워커 실가동 점검에서 찾은 세션 연결·Redis 장애 폴백·compose 플래그 수정` |
| **커밋 번호 (SHA)** | `731143ef853d0497aef7fda18541f025faa36426` |
| **짧은 SHA** | `731143e` |
| **브랜치** | `feature/celery-worker` |
| **부모 커밋** | `2459784` |

## 2. 주 커밋 내용

- 워커용 DB 세션 `_default_session()` — lifespan 없이도 엔진에 스스로 바인딩
- `enqueue_batch` 가 Redis 장애 시 예외·무한 대기 대신 경고 로그 후 `False` 반환 → BackgroundTasks 폴백
- `docker-compose.yml`: backend 에 `BATCH_USE_CELERY` 전달, `CELERY_CONCURRENCY`, 실행 명령 주석
- `.env.example` 안내: backend·celery_worker 둘 다 같은 값 필요
- 테스트 3건 추가(폴백 · celery 큐잉 · 워커 세션 바인딩)

## 3. 상세 내용

### 3.1 배경 / 목적
인수인계(Grok) 남은 일 "Celery 워커 실가동"을 실제 Docker 로 돌려 확인. 코드만 읽어서는 안 보이던 문제 3개가 나왔다.

### 3.2 발견한 문제
| 문제 | 영향 |
|------|------|
| 워커 프로세스엔 FastAPI lifespan 이 없어 `SessionLocal` 이 엔진에 안 묶임 | 워커가 DB 를 못 열어 작업이 queued 로 영구 정체 |
| Redis 가 죽으면 `.delay()` 가 멈추거나 예외 | 업로드 요청이 멈추거나 500 |
| compose 의 플래그가 celery_worker 에만 있고 backend 엔 미전달 | backend 가 계속 in-process 처리 → 워커가 놀고 있음 |

### 3.3 변경 범위
- 수정: `backend/app/tasks/batch_tasks.py`, `docker-compose.yml`, `.env.example`, `tests/unit/test_batch_api.py`

### 3.4 의도적으로 하지 않은 것
- Redis 장애 시 재시도 큐·알림, 워커 자동 확장 (운영 단계에서 결정)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] Docker 확인: MariaDB · Redis · backend · celery_worker (`--profile phase2`, `BATCH_USE_CELERY=true`, onnx 슬림 이미지)
- [x] e2e: 회원 배치 3장(1장 깨진 파일) 등록 응답 0.26s(`queued`) → 워커 처리 12.8s → `done` "완료 (실패 1/3)" → 항목 `ok/failed/ok`(onnx) → zip 에 성공 2건
- [x] 백엔드 단위 테스트 통과
- 점검용 테스트 계정·배치는 실행 후 삭제 확인(남은 배치 0)

### 4.2 부작용 / 리스크
- 워커 동시성 기본 1(GPU 메모리 보호). 올리면 모델이 프로세스마다 로드됨

### 4.3 후속 작업
- Grounding DINO + SAM2 가중치·활성화 점검, 클라우드 LLM 스모크(키 필요)
- 전체 작업 후 총 병합(develop, `--no-ff`, 쌓인 순서)

### 4.4 관련 문서
- `docs/API_DOCUMENTATION.md`(Batch), `docs/branchs/commits/261007_1136_d80b809_batch-pipeline-results_feature-batch-api.md`
