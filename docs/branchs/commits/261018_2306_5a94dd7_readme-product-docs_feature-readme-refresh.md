# 제품 · 배포 README 를 소개 문서로 다시 씀 / `5a94dd7e794ba11ba14de754bcb3cc4d2580649b`

> 브랜치: `feature/readme-refresh`  
> 작성일: `2026-10-18 23:06`  
> 작성자: `agent`  
> 파일명: `261018_2306_5a94dd7_readme-product-docs_feature-readme-refresh.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(readme): 제품 · 배포 README 를 소개 문서로 다시 씀` |
| **커밋 번호 (SHA)** | `5a94dd7e794ba11ba14de754bcb3cc4d2580649b` |
| **짧은 SHA** | `5a94dd7` |
| **브랜치** | `feature/readme-refresh` |
| **부모 커밋** | `cc789195488dad574b1b209a3fa29596e9bdce9c` |

## 2. 주 커밋 내용

- 루트 `README.md` 를 프로젝트 소개 문서로 다시 씀 — 문제 정의 · 기능 · 처리 흐름(mermaid) · 시스템 구성 · 기술 스택 · AI · 학습 순환 · 데이터 · 보안 · 실행 · 구조 · 테스트 · 문서 지도 · 개발 방식 · 남은 일
- `frontend` · `backend` · `console` README 를 화면 · 계층 · API · 설정 · 실행 · 한계까지 담는 긴 안내로 다시 씀
- `Portfolio` · `Portfolio/ai` · `Portfolio/site` README 에 구성 · 안내 챗 · 깊이 추론 규칙 · Vercel + PC Flask + Cloudflare 임시 터널 배포 순서를 기록
- `docker` · `deploy` · `scripts` · `tests` README 에 빠졌던 서비스 · 스크립트 · 테스트 파일을 채움
- `data` · `models` · `logs` · `backend/data` · `backend/models` · `backend/logs` README 를 실제 폴더 · 설정과 맞춤

## 3. 상세 내용

### 3.1 배경 / 목적

사용자가 README 가 너무 부실하다며 전체를 길게 소개하는 내용으로 고도화해 달라고 요청했다.
기존 README 는 표 위주라 처음 보는 사람이 프로젝트의 목적과 구조를 이해하기 어려웠고, 일부는 실제와 달랐다.

### 3.2 변경 범위

- 수정된 경로 (17개): `README.md`, `frontend/README.md`, `backend/README.md`, `console/README.md`, `Portfolio/README.md`, `Portfolio/ai/README.md`, `Portfolio/site/README.md`, `docker/README.md`, `deploy/README.md`, `scripts/README.md`, `tests/README.md`, `data/README.md`, `models/README.md`, `logs/README.md`, `backend/data/README.md`, `backend/models/README.md`, `backend/logs/README.md`
- 추가 · 삭제된 경로: 없음

### 3.3 기술 포인트

- 내용은 `docs/HANDOVER.md` · `docs/FEATURES.md` · `Portfolio/markdown/*` 와 실제 코드(`docker-compose*.yml` · `.env.example` · `backend/app/core/config.py` · 라우터 · `frontend/src/api/client.ts` · `Portfolio/ai/app.py` 등)를 대조해 썼다
- 바로잡은 낡은 내용
  - 예전 경로 `d:\my_project\CutNKeep` 제거
  - 업로드 정리: `scripts/cleanup.py` 수동 → 백엔드가 매시간 자동
  - 사용자 앱 업로드 제한 시간 180초 → 실제 300초 (GIF · 영상 600초)
  - docker README 에 없던 `mailpit` · `mariadb-backup` · `celery_worker` · HTTPS · PC Ollama · GPU 오버레이 추가
  - `scripts/experiments` 의 `davis_eval` · `gif_matte_eval` · `parser_compare` · `video_removal_eval` · `video_tracking_eval`, `scripts/chroma_embed.py` 추가
  - tests README 에 빠진 테스트 파일(`test_docs_coverage.py` · `test_chroma_feedback.py` · `test_deploy_tools.py` 등) 추가
  - `training/yolo/apply_best.py` 의 기본 대상 이름이 아직 `yolo26s-seg.pt` 라 `--dest` 를 쓰라고 명시
- 추정이 섞였던 문장은 코드로 확인해 고쳤다 (Flask 안내의 질문 분류는 검색 필터가 아니라 가산점, SQLite 손상 파일 이름 바꾸기는 자동 기능이 아님)
- `backend/README.md` 설정 표에 `PROMPT_CHROMA_ENABLED` · `PROMPT_CHROMA_MIN_SCORE` · `PROMPT_CHROMA_DIR` · `PROMPT_CHROMA_SHARED_DIR` 설명을 넣어 문서 등록 검사의 "문서에 설명 없는 설정" 실패를 해결

### 3.4 의도적으로 하지 않은 것

- `.env.example` 에 `PROMPT_CHROMA_*` 4개 추가 — README 범위 밖이라 손대지 않음
- 코드 주석(`docker-compose.yml` 머리의 서비스 DB 설명 등) 수정
- `docs/*` 하위 · 에이전트 설정 폴더 · Chroma 폴더 README — 다음 커밋

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `pytest tests/structure` — 13개 중 12개 통과. 남은 1개(`test_every_setting_is_in_env_example`)는 `develop` 에서도 같은 기존 실패
- [x] 바꾼 README 17개의 상대 링크 검사 — 깨진 링크 0
- [ ] Docker 확인 — 해당 없음 (문서만 변경)
- 결과 서술: 문서만 바꿨고 코드 · 설정은 그대로다

### 4.2 부작용 / 리스크

- README 의 수치(테스트 수 · 실험 수치)는 2026-10-12 인수인계 기준이다. 테스트가 늘면 함께 고쳐야 한다
- 공개 주소 · 서버 IP 가 루트 README 에 있다 (이미 `docs/HANDOVER.md` 에 공개된 값)

### 4.3 후속 작업

- `docs/*` 하위 README · 에이전트 설정 폴더 README · Chroma 폴더 README 보강
- `.env.example` 의 `PROMPT_CHROMA_*` 누락은 사용자 확인 후 별도 작업
- 병합은 전체 작업이 끝난 뒤 사용자 지시로

### 4.4 관련 문서

- `docs/HANDOVER.md` · `docs/FEATURES.md` · `tests/structure/test_docs_coverage.py`
