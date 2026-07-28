# 컷앤킵 (Cut & Keep)

프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

## 문서

| 문서 | 설명 |
|------|------|
| [docs/plan/LOGIC_STRUCTURE.md](docs/plan/LOGIC_STRUCTURE.md) | **통합 로직 구조 (구현 1순위)** |
| [docs/plan/AI_MODEL_STRATEGY.md](docs/plan/AI_MODEL_STRATEGY.md) | **yolo26s-seg · Ollama E4B · OpenAI/Gemini** |
| [docs/plan/PROJECT_STRUCTURE.md](docs/plan/PROJECT_STRUCTURE.md) | 폴더·모듈 구조 |
| [docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md](docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md) | 실행 규칙 + Git |
| [docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md](docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md) | 환경·실행·배포 |

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

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
| [scripts/](./scripts/README.md) | ✅ | ONNX 변환, cleanup 등 |
| [training/](./training/README.md) | ✅ | **YOLO detect/seg · LoRA 학습 구역** |
| [tests/](./tests/README.md) | ✅ | **pytest 실행 전 검증** |
| [data/](./data/README.md) | ✅ | 업로드·피드백·SQLite |
| [models/](./models/README.md) | ✅ | 추론용 가중치 (git ignore) |
| [logs/](./logs/README.md) | ✅ | 런타임 로그 |
| [docs/](./docs/README.md) | ✅ | 문서 허브 |
| [docker/](./docker/README.md) | ✅ | Compose 메모 |
| [Scribble/](./Scribble/README.md) | ✅ | 개인 메모 (내용 ignore) |

## 아키텍처 요약

```
frontend(:5173) ─┐
console(:5174)  ─┼→ backend(:8000) → Repositories → SQLite | MariaDB
                 └→ files: data/uploads, data/feedback
```

처리 파이프라인: **보안 검증 → 프롬프트 분석 → 전처리 → 세그멘테이션 → 효과 → 검증 → DB 저장 / 피드백**

계층: `schemas` · `routers` · `repositories` · `models`(ORM) · `db`  
DB 설계: [docs/plan/DATABASE.md](docs/plan/DATABASE.md)  
운영 콘솔: [console/README.md](console/README.md) · [docs/guidance/console-admin.md](docs/guidance/console-admin.md)



## Phase

| Phase | 범위 |
|-------|------|
| **1 (현재)** | 단일 이미지, YOLO-seg ONNX, LangGraph 기본, 피드백 UI |
| **2** | Grounding DINO + SAM2, 배치 500장, LoRA |
| **3** | 영상 + Temporal Smoothing, Docker 배포 고도화 |

## 라이선스

Private / 프로젝트 소유자 기준
