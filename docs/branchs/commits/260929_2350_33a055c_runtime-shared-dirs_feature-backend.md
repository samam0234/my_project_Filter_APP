# 서비스 런타임과 학습 공유 폴더 분리 / `33a055cea053d8fa2b39d8ecbdb5af38496612d2`

> 브랜치: `feature/backend`  
> 작성일: `2026-09-29 23:50`  
> 작성자: `agent`  
> 파일명: `260929_2350_33a055c_runtime-shared-dirs_feature-backend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(backend): 서비스 런타임과 학습 공유 폴더 분리` |
| **커밋 번호 (SHA)** | `33a055cea053d8fa2b39d8ecbdb5af38496612d2` |
| **짧은 SHA** | `33a055c` |
| **브랜치** | `feature/backend` |
| **부모 커밋** | `027f06d` (develop) |

## 2. 주 커밋 내용

- `backend/data`·`logs`·`models` 를 서비스 런타임 전용으로 실제 사용
- 루트 `data`·`models`·`logs` 는 학습 공유 자산 (feedback·pseudo_labels·모델 원본/후보·학습 로그)
- `Settings.resolve_runtime_path` / `resolve_shared_path` 로 경로 기준 분리
- 백엔드 파일 로그 신설: `backend/logs/app_YYYY-MM-DD.log` (자정 회전, 14일, UTF-8)
- docker-compose 마운트·`apply_best.py`·`cleanup.py` 를 새 구조에 맞춤
- 경로 분리 단위 테스트 3개 + 폴더 README·plan 문서 갱신

## 3. 상세 내용

### 3.1 배경 / 목적

`backend/data`·`logs`·`models` 는 `.gitkeep` 만 있는 빈 틀이었다.
로컬은 `_project_root()` 가 저장소 루트를, Docker 는 compose 가 루트 폴더를 마운트해
어디서도 쓰이지 않았다. 파일 로그도 없어 stderr 로만 남았다.
서비스가 만들고 서비스만 쓰는 데이터와, 학습이 읽는 데이터를 폴더로 구분한다.

### 3.2 변경 범위

- 추가된 경로:
  - `backend/data/README.md`, `backend/logs/README.md`, `backend/models/README.md`
- 수정된 경로:
  - `backend/app/core/config.py` (경로 기준 분리, `LOG_DIR`·`LOG_RETENTION_DAYS`)
  - `backend/app/db/session.py` (SQLite 경로 = 런타임 기준)
  - `backend/app/utils/logging.py`, `backend/app/main.py` (파일 로그, 기동 로그에 경로 표시)
  - `docker-compose.yml`, `.dockerignore`, `.gitignore`, `.env.example`
  - `training/yolo/apply_best.py` (배포 대상 `backend/models/`)
  - `scripts/cleanup.py` (정리 대상 `backend/data/uploads/`)
  - `data/README.md`, `models/README.md`, `logs/README.md`, `RUN.md`
  - `docs/plan/CURRENT_STACK.md` (9절 신설), `docs/plan/PROJECT_STRUCTURE.md`
  - `tests/unit/test_config.py`
- 삭제된 경로:
  - `backend/data/feedback/.gitkeep`, `backend/data/pseudo_labels/.gitkeep` (학습 공유는 루트)

### 3.3 기술 포인트

| 역할 | 경로 | 기준 |
|------|------|------|
| 서비스 런타임 | `backend/data/uploads`, `backend/data/cutnkeep.db`, `backend/models`, `backend/logs` | `backend/` |
| 학습 공유 | `data/feedback`, `data/pseudo_labels`, `models/`(원본·후보·LoRA), `logs/` | 저장소 루트 |

- `.env` 의 상대 경로 값(`data/uploads`, `models/yolo26s-seg.pt` 등)은 그대로 두고 **해석 기준만** 바뀜
- Docker 는 `/app` 이 둘 다의 기준이므로 compose 에서 `./backend/data` → `/app/data` 위에
  `./data/feedback` → `/app/data/feedback` 을 중첩 마운트해 같은 분리를 유지
- 런타임 산출물은 `.dockerignore` 로 이미지에 굽지 않음
- 파일 로그는 `enqueue=True` (요청 스레드 안전), `encoding=utf-8` (Windows cp949 무관)

### 3.4 의도적으로 하지 않은 것

- 학습·스크립트의 파일 로깅 자동화 (루트 `logs/` 는 리다이렉트 사용 안내만)
- 루트 `data/uploads`·`data/cutnkeep.db` 원본 삭제 (복사만, 확인 후 수동 정리)
- `convert_to_onnx.py` 기본 경로 정리

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 전체 통과 (신규 경로 테스트 3개 포함)
- [x] 로컬 실행 확인 — `--reload` 서버에서 새 경로로 기동
- [ ] Docker 확인 (Docker Desktop 꺼져 있어 미실시)
- [x] API 스모크
  - 기존 데이터 이전: jobs 10건·feedbacks 1건·uploads 10개를 `backend/data` 로 복사,
    DB 의 before/after 절대 경로를 새 위치로 갱신 (미존재 0건)
  - `GET /api/v1/jobs`·`/files/{id}/before` 200
  - 업로드 1건: 결과가 `backend/data/uploads/` 에만 생성, 모델은 `backend/models/yolo26s-seg.pt` 로드
  - `backend/logs/app_2026-09-29.log` 에 한글 로그 정상 기록

### 4.2 부작용 / 리스크

- 이 브랜치 체크아웃 전후로 `--reload` 서버가 보는 DB·모델 위치가 바뀜
  (develop 이하 브랜치는 루트 `data/`, 이 브랜치는 `backend/data/`)
- 다른 PC 에서는 `backend/models/` 에 가중치를 새로 배치해야 함 (`apply_best.py` 또는 수동 복사)
- Docker 중첩 마운트 시 호스트에 빈 `backend/data/feedback` 등 마운트 지점 폴더가 생길 수 있음 (gitignore 처리)

### 4.3 후속 작업

- `feature/llm` 과 함께 develop 병합 (`config.py` 서로 다른 구간 수정, 충돌 가능성 낮음)
- Docker Desktop 기동 후 compose 마운트 검증
- 확인 후 루트 `data/uploads/*`, `data/cutnkeep.db` 정리

### 4.4 관련 문서

- `docs/plan/CURRENT_STACK.md` 9절
- `backend/data/README.md`, `backend/models/README.md`, `backend/logs/README.md`
