# 컷앤킵 (Cut & Keep)

프롬프트로 원하는 대상만 남기고 배경을 제거하는 지능형 필터 앱

## 문서

| 문서 | 설명 |
|------|------|
| [docs/plan/LOGIC_STRUCTURE.md](docs/plan/LOGIC_STRUCTURE.md) | **통합 로직 구조 (구현 1순위)** |
| [docs/plan/PROJECT_STRUCTURE.md](docs/plan/PROJECT_STRUCTURE.md) | 폴더·모듈 구조 |
| [docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md](docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md) | 실행 규칙 + Git |
| [docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md](docs/plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md) | 환경·실행·배포 |

## 빠른 시작 (Phase 1)

```bash
# 환경변수
cp .env.example .env

# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (사용자 앱)
cd frontend
npm install
npm run dev

# Console (운영 관리자)
cd console
npm install
npm run dev
```

| 앱 | URL |
|----|-----|
| Backend API docs | http://localhost:8000/docs |
| Frontend (사용자) | http://localhost:5173 |
| **Console (운영)** | http://localhost:5174 |

문서 허브: [docs/README.md](docs/README.md)  
커밋 규칙: [docs/guidance/commit-message.md](docs/guidance/commit-message.md) (제목 영어 / 본문·바닥글 한국어)  
브랜치 규칙: [docs/guidance/branch-merge.md](docs/guidance/branch-merge.md) (작업=feature, 일자 병합=develop/main)  
에이전트 스킬: [.agents/SKILL.md](.agents/SKILL.md)



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
