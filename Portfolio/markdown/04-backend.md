# 백엔드 서버

## 개요

백엔드는 저장소 `backend/`의 FastAPI다. 포트는 8000이다.
요청을 받고, 문장을 구조로 바꾸고, 대상 마스크를 만들고, 효과를 적용하고, 회원에게만 기록한다.

계층은 고정이다.

| 계층 | 경로 | 책임 |
|------|------|------|
| Router | `app/routers/` | HTTP, 권한, 응답 |
| Schema | `app/schemas/` | Pydantic 요청과 응답 |
| Service, Workflow | `app/services/`, `app/workflows/` | 처리와 파일 |
| Repository | `app/repositories/` | SQL |
| Model | `app/models/` | 테이블 |
| DB | `app/db/` | 엔진과 세션 |

라우터는 SQL을 직접 쓰지 않는다. 레포지토리는 OpenCV와 LLM을 모른다. ORM 모델과 API 스키마를 섞지 않는다.

로컬 개발 서버는 uvicorn이다. Docker 프로젝트 이름은 `cut_and_keep`이다.
서비스는 frontend, backend, mariadb, redis, adminer, mariadb-backup이다.
celery 워커는 Compose 프로필 `phase2`일 때만 있다. 기본 배치는 API 프로세스 안에서 한 장씩 처리한다.
HTTPS는 `docker-compose.https.yml`의 Caddy, PC Ollama는 `docker-compose.pc-ollama.yml`의 브리지, GPU는 `docker-compose.gpu.yml`이다.

운영 서버는 Oracle Cloud A1.Flex, ARM 4 OCPU, 메모리 24GB, Ubuntu 24.04다.
저장소 브랜치는 서버에서 `main`이다. 공개 포트는 22, 80, 443뿐이다.

## 엔진

| 영역 | 선택 |
|------|------|
| API | FastAPI 0.143, Starlette 1.7, Pydantic 2, Uvicorn |
| 언어 | Python 3.10에서 3.12. 의도한 런타임은 3.11 |
| ORM | SQLAlchemy 2 |
| 서비스 DB | Docker는 MariaDB 11. 호스트 개발은 SQLite `cutnkeep.host.db` |
| 학습 DB | MariaDB. 꺼져 있으면 SQLite로 잠시 대체하고, 다시 켜면 동기화 |
| 큐 | Redis 7. 호스트 6380. Celery 5.4는 선택 |
| 이미지 | OpenCV. 전처리, 마스크, 경계, Telea |
| 세션 | scrypt 비밀번호, HttpOnly 쿠키 |

`/health`의 phase 상수는 1이다. 기능이 Phase 2와 3까지 들어가 있어도 이 숫자는 바꾸지 않는다. 스모크 테스트가 그 값을 확인한다.
이미지와 영상은 DB에 넣지 않는다. 경로만 기록한다.

기동 시 세그 모델을 올리고 빈 이미지로 한 번 추론한다. 로컬 측정에서 첫 요청이 약 71초에서 약 4.5초로 줄었다.
처리 중에도 `/health`는 스레드풀 때문에 바로 응답한다. YOLO 추론 자체는 잠금으로 한 번에 하나다.

## 기능

파이프라인 노드는 `prompt_analyzer`, `preprocessor`, `segmentor`, `validator`, `effect_applier`, `feedback_collector`다.

| 효과 | 코드 값 | 결과 |
|------|---------|------|
| 남기고 배경 제거 | `remove_bg` | 투명 PNG, GIF, WebP |
| 배경 블러 | `blur` | 강도 0에서 100. 문장에 숫자가 없으면 15 |
| 크롭 | `crop` | 대상 주변으로 자름 |
| 대상 지우기 | `remove_object` | 사진 LaMa, 없으면 Telea. 영상은 배경판 |

인스턴스 선택은 규칙이다. 위치, 순서, 개수, 크기, 색과 부위.
지정하지 않은 대상이 마스크에 섞이지 않게 다른 인스턴스 영역을 빼는 것이 기본이다. GrabCut과 CLAHE는 섞임 때문에 기본이 꺼져 있다.

검증은 ok, fallback, failed다. 실패에 가까우면 전처리 조건을 반대로 하고 신뢰도 기준을 낮춰 한 번 더 찾는다. 더 나쁜 마스크면 첫 시도를 유지한다.
빈 마스크는 "요청한 대상을 찾지 못함"과 그때 보인 라벨을 알려 준다.

영상은 프레임마다 같은 규칙을 적용한다. 위치나 순서로 고른 대상은 첫 프레임의 그 대상을 끝까지 따라간다.
광학 흐름으로 마스크 흔들림을 줄인다. 오디오는 mp4에 남긴다. ffmpeg가 없으면 webm에서 avi로 안내한다.
GIF는 간격과 반복을 유지한다. 배경 제거는 투명 GIF와, 경계가 부드러운 WebP를 같이 준다.

회원 파일은 24시간 뒤 매시간 지운다. 점(.)으로 시작하는 파일은 지우지 않는다.
처리에 실패했거나 인식이 불확실한 회원 요청의 원본은 30일간 실패 사진으로 두고, 계정 삭제 시 바로 지운다.
서버 로그는 14일이다. MariaDB 덤프는 매일, 7일간, 같은 디스크다.

## API

접두사는 `/api/v1`이다. 운영의 Swagger는 열지 않는다.

| 묶음 | 대표 |
|------|------|
| 상태 | `GET /health` |
| 사진 | `POST /upload`, `GET /files/{id}/*` |
| GIF | `POST /gif` |
| 영상 | `POST /video`, `GET /video/{id}` |
| 기록 | `GET /jobs`, `GET /jobs/{id}` |
| 피드백 | `POST /feedback` |
| 배치 | `POST/GET /batch`, 항목, zip |
| 계정 | `/auth/signup/start`, `/signup/verify`, `/login`, `/me`, 찾기, 탈퇴 |
| 모델 | `GET /llm/models` |
| 채팅 | `POST /chat` |
| 콘솔 | `/console/me`, jobs, batches, learning, users, system |

결과 파일과 기록은 소유자가 아니면 404다. 없는 것과 남의 것을 구분하지 않는다.
속도 제한은 비로그인 IP와 회원 계정을 나눈다. nginx 뒤에서는 신뢰하는 프록시의 실제 IP를 쓴다.
Worker가 넘긴 실제 IP는 `EDGE_SECRET`이 맞을 때만 믿는다.
업로드는 확장자, MIME, 시그니처, 해상도를 본다. 사진은 약 20MB, 영상은 80MB다.

production에서 위험한 기본값이면 프로세스가 뜨지 않는다. 점검 코드는 `app/core/preflight.py`다.
운영 `.env`는 `scripts/make_prod_env.py`가 비밀 값을 채워 만들고, 그 파일은 서버에만 둔다.

## 화면이 아니라 동작으로 보는 내부

백엔드에는 사용자용 HTML 페이지가 거의 없다. 내부는 로그, Swagger(개발), 콘솔이 대신 보여 준다.
포트폴리오의 백엔드 장에 넣는 스크린샷은 그래서 콘솔의 시스템 화면과 헬스, 그리고 처리 결과가 나온 사용자 화면이다.
설정이 맞게 떠 있는지는 시스템 화면의 세그 런타임, 지우기 엔진, 해석 체인, 배치 큐로 확인한다.

파일 위치는 둘로 나뉜다.

| 종류 | 위치 |
|------|------|
| 회원 업로드 | `backend/data/uploads`, 영상은 `uploads/videos` |
| 서빙 가중치 | `backend/models` (Git 밖) |
| 런타임 로그 | `backend/logs` |
| 학습 사이드카 | 저장소 `data/feedback`, `data/pseudo_labels` |
| DB 데이터와 덤프 | `data/mariaDB_datas`, `data/mariaDB_backups` |

호스트에서 직접 띄운 백엔드와 Docker 백엔드가 같은 SQLite 파일을 쓰면 손상된 적이 있다. 파일을 나눠 둔 이유가 그것이다.
MariaDB 접속에 `172.18.0.x`를 호스트 주소로 쓰지 않는다. 그 대역은 Docker 안쪽이다.
비밀번호 인증만 쓴다. GSS와 Kerberos는 쓰지 않는다.

## 고급 처리와 그 경계

이 서버가 직접 하는 고급 처리는 다음이다.

- LangGraph로 노드 상태와 재시도를 관리한다.
- LangChain 해석 체인이 LLM 답과 키워드 파서를 비교한다.
- RAG는 승인된 문장을 예시로 붙인다. 글자 n-gram으로 찾고, 루트 `data/chroma`와 `backend/data/chroma`의 확인 문장을 한 건 더할 수 있다. 임베딩 모델은 따로 받지 않는다.
- 선택적 LoRA는 같은 프로세스에서 Qwen2.5-1.5B 어댑터를 돌린다. GPU가 있을 때의 선택이다.
- ONNX Runtime 경로는 torch 없이 YOLO 세그를 돌린다. 슬림 이미지는 약 1.1GB다. ultralytics 이미지는 약 2.8GB다.

클라우드 LLM(OpenAI, Gemini)은 설정으로 연결되어 있으나 운영 기본값이 아니다.
그 값으로 바꾸면 사용자 문장이 밖으로 나간다. 개인정보 처리방침도 같이 고쳐야 한다.

## 문제와 개선

운영에서 확인된 한계:

- 문장 해석이 PC Ollama에 의존한다. 터널이 끊기면 키워드 파서다. GPU 서버가 근본 대응이다.
- ARM 서버에서는 GPU 오버레이와 LoRA 해석을 쓰지 않는다.
- 서버 밖 백업이 없다.
- 스키마 변경은 기동 시 `create_all`과 제한된 `ALTER`다. Alembic은 아직이다.
- Celery 워커는 코드와 프로필만 있고, 기본 운영 경로는 아니다.
- 오픈 보캐브 가중치는 없다. 플래그는 꺼져 있다. 없는 상태에서 켜면 동작하지 않는다.
- 움직이는 카메라의 영상 지우기는 일부 클립이 아직 예전 방식이다.
- nginx가 옛 백엔드 IP를 붙들고 502가 난 적이 있다. resolver로 고쳤다.
- 전체 `docker compose up`은 개발용 Adminer까지 띄운다. 운영은 서비스를 지정한다.

추가하려는 서버:

- GPU가 있는 추론 서버. LoRA와 오픈 보캐브를 운영에 올릴 때.
- 서버 밖 백업 저장.
- 필요해지면 클라우드 LLM은 문장만 보내는 보조 해석. 사진을 보내지 않는 현재 원칙은 유지한다.

## 이후 방향

백엔드는 공개면이 작아야 한다. 80과 443만 밖에 두고, 데이터베이스와 Redis와 Adminer는 루프백이다.
기능이 늘어도 비로그인은 저장하지 않는 규칙, 회원 파일 24시간, 실패 사진 30일, 콘솔은 관리자만이라는 규칙을 먼저 문서와 맞춘다.
처리방침과 코드의 보관 기간이 어긋난 적이 있어, 기간을 바꾸는 커밋은 화면 문구를 같이 고친다.
