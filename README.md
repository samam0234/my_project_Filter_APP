# 컷앤킵 (Cut & Keep)

프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

## 할 수 있는 것

| 기능 | 예시 문장 | 결과 |
|------|-----------|------|
| 원하는 것만 남기기 | "강아지만 남기고 배경 제거" | 투명 PNG (배경 블러 · 크롭도) |
| 특정 한 명·하나 고르기 | "맨 앞 빨간 안전모 쓴 사람만", "왼쪽에서 두 번째 사람" | 위치 · 순서 · 개수 · 색으로 고름 |
| 필요 없는 것 지우기 | "오른쪽 사람 지워줘" | 학습형 인페인팅(**LaMa**)으로 주변 무늬를 이어 그려 메움 |
| 배경 덩어리 | "건물만 남기고 하늘 블러" | 건물 · 하늘 · 도로 등 14종 (SegFormer) |
| **움직이는 GIF** | 작업실 GIF 탭 | 프레임마다 처리, 투명 GIF + 부드러운 경계 WebP |
| **짧은 영상** | 영상 화면 (최대 20초) | H.264 mp4, 프레임 사이 흔들림 보정 |
| 배치 (회원) | 같은 문장으로 최대 500장 | zip 으로 받기 |
| 작업 기록 (회원) | 사진 · 영상 · GIF 를 모아 보기 · 다시 받기 · 평가/정답 알려주기 | 교정 문장은 검수 후 학습(RAG · LoRA) |

비로그인도 바로 처리·다운로드할 수 있고(서버에 남기지 않음), 회원 파일은 서버에 24시간 보관 후 자동으로 지워진다.

## 문서

| 문서 | 설명 |
|------|------|
| [docs/FEATURES.md](docs/FEATURES.md) | **전체 기능 목록** — 화면 · API · 설정 · 코드 · 문서 |
| [docs/plan/CURRENT_STACK.md](docs/plan/CURRENT_STACK.md) | **현재 포트·DB·Docker 스냅샷** |
| [docs/plan/LOGIC_STRUCTURE.md](docs/plan/LOGIC_STRUCTURE.md) | 통합 로직 구조 |
| [docs/plan/AI_MODEL_STRATEGY.md](docs/plan/AI_MODEL_STRATEGY.md) | **yolo26m-seg · Ollama E4B · OpenAI/Gemini** |
| [docs/plan/PROJECT_STRUCTURE.md](docs/plan/PROJECT_STRUCTURE.md) | 폴더·모듈 구조 |
| [docs/plan/DATABASE.md](docs/plan/DATABASE.md) | SQLite / MariaDB |
| [docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md](docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md) | 실행 규칙 + Git |
| [docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md](docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md) | 환경·실행·배포 |
| [training/README.md](training/README.md) | YOLO 학습 · 실행 전 설정 |
| [RUN.md](./RUN.md) | 로컬 3터미널 + Docker 실행 |
| [docs/guidance/security.md](docs/guidance/security.md) | **배포 전 보안·운영 점검표** |
| [docs/guidance/learning-loop.md](docs/guidance/learning-loop.md) | 새 학습 내용이 RAG · LangChain · LangGraph · LoRA 로 들어가는 경로 |
| [docs/vaildates/README.md](docs/vaildates/README.md) | 검증·실험 결과 모음 (수치 근거) |

## 빠른 시작 (Phase 1)

**상세 실행 · 서버 가이드 → [RUN.md](./RUN.md)** (로컬 3터미널 + Docker)

```bash
# 환경변수
cp .env.example .env

# Backend (의존성은 저장소 루트 requirements.txt)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000   # 다른 기기에서 열 때만 0.0.0.0

# Frontend (사용자 앱)
cd ../frontend
npm install
npm run dev

# Console (운영 관리자)
cd ../console
npm install
npm run dev
```

| 앱 | URL |
|----|-----|
| Backend API docs | http://localhost:8000/docs |
| Frontend (사용자) | http://localhost:5173 |
| **Console (운영)** | http://localhost:5174 |

**Docker** (사용자 앱은 nginx 로 http://localhost) — 자세히는 [docs/guidance/docker-run.md](docs/guidance/docker-run.md)

```bash
docker compose -p cut_and_keep --env-file .env up -d --build
# 호스트에서 uvicorn 을 따로 띄워 8000 이 차 있으면: BACKEND_PORT=8001 docker compose -p cut_and_keep --env-file .env up -d
```

backend · MariaDB · Redis · Adminer 포트는 이 PC(127.0.0.1)에만 열린다 (`BIND_HOST`). 공개는 :80 하나.

문서 허브: [docs/README.md](docs/README.md)  
실행 가이드: [RUN.md](./RUN.md)  
테스트: [tests/README.md](./tests/README.md) · [docs/plan/TESTING.md](./docs/plan/TESTING.md)  
커밋 규칙: [docs/guidance/commit-message.md](docs/guidance/commit-message.md) (type/scope 영어 · 제목 요약·본문·바닥글 한국어)  
브랜치 규칙: [docs/guidance/branch-merge.md](docs/guidance/branch-merge.md) (작업=feature, 일자 병합=develop/main)  
에이전트 스킬: [.agents/skills/cutnkeep/SKILL.md](.agents/skills/cutnkeep/SKILL.md) · [AGENTS.md](./AGENTS.md)  
개인 메모: [Scribble/README.md](./Scribble/README.md) (내용물 git ignore)



## 주요 폴더

| 폴더 | README | 역할 |
|------|--------|------|
| [backend/](./backend/README.md) | ✅ | FastAPI API · 파이프라인 · DB |
| [frontend/](./frontend/README.md) | ✅ | 사용자 웹 앱 (:5173) |
| [console/](./console/README.md) | ✅ | 운영 콘솔 (:5174) |
| [scripts/](./scripts/README.md) | ✅ | ONNX 변환, 정리, LoRA 재학습, 실험 평가 |
| [training/](./training/README.md) | ✅ | **YOLO detect/seg · LoRA 학습 구역** |
| [tests/](./tests/README.md) | ✅ | **pytest 실행 전 검증** |
| [data/](./data/README.md) | ✅ | 업로드·피드백·SQLite |
| [models/](./models/README.md) | ✅ | 추론용 가중치 (git ignore) |
| [logs/](./logs/README.md) | ✅ | 런타임 로그 |
| [docs/](./docs/README.md) | ✅ | 문서 허브 |
| [docker/](./docker/README.md) | ✅ | Compose · MariaDB(password) · Adminer |
| [Scribble/](./Scribble/README.md) | ✅ | 개인 메모 (내용 ignore) |

**GitHub 홈 README = 이 파일.** `.github/Read_for_we.md` 는 내부 안내용이며 홈 소개가 아니다.

## 아키텍처 요약

```
frontend(:5173 · Docker :80 nginx) ─┐
console(:5174)                       ─┼→ backend(:8000) → Repositories → 서비스 DB SQLite (+ 자동 백업)
                                      │                                 → 학습 DB MariaDB
                                      └→ files: backend/data/uploads (24시간 뒤 자동 정리) · data/feedback (학습 공유)
```

처리 파이프라인 (LangGraph): **보안 검증 → 프롬프트 분석(LLM + 키워드 파서 다수결, LangChain) → 전처리 → 세그멘테이션(YOLO26m-seg · SegFormer, 겹침 덜어내기) → 검증·재시도 → 효과(배경 제거 · 블러 · 크롭 · LaMa 지우기) → DB 저장 / 피드백**

계층: `schemas` · `routers` · `repositories` · `models`(ORM) · `db`  
DB 설계: [docs/plan/DATABASE.md](docs/plan/DATABASE.md)  
운영 콘솔: [console/README.md](console/README.md) · [docs/guidance/console-admin.md](docs/guidance/console-admin.md)



## Phase

| Phase | 범위 |
|-------|------|
| **1** ✅ | 단일 이미지, YOLO-seg, LangGraph, LLM 프롬프트 분석(Ollama · LoRA), 특정 인스턴스 선택 · 물체 지우기, 피드백 UI |
| **2** ✅ | 배치 500장, 영상(mp4 · 작업 기록), **GIF**(투명 GIF + WebP), 배경 덩어리(SegFormer), 학습형 지우기(**LaMa**), 해석 체인(LangChain 다수결), LoRA 재학습 루프, Grounding DINO + SAM2(코드 있음·가중치 필요) |
| **3** (진행) | 영상 프레임 간 흐름 보정(✅ 광학 흐름 스무딩) · 추적(LSTM 등), 배포(HTTPS · SMTP · 개인정보 처리방침 — [security.md](docs/guidance/security.md)), YOLO 재학습(승인 데이터가 쌓이면) |

## 라이선스

Private / 프로젝트 소유자 기준
