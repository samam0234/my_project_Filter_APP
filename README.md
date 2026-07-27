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

# Frontend (다른 터미널)
cd frontend
npm install
npm run dev
```

- Backend API docs: http://localhost:8000/docs  
- Frontend: http://localhost:5173  

## 아키텍처 요약

```
Frontend (React) → FastAPI → LangGraph workflow → Services (OpenCV / YOLO / effects)
```

처리 파이프라인: **보안 검증 → 프롬프트 분석 → 전처리 → 세그멘테이션 → 효과 → 검증 → 피드백**

## Phase

| Phase | 범위 |
|-------|------|
| **1 (현재)** | 단일 이미지, YOLO-seg ONNX, LangGraph 기본, 피드백 UI |
| **2** | Grounding DINO + SAM2, 배치 500장, LoRA |
| **3** | 영상 + Temporal Smoothing, Docker 배포 고도화 |

## 라이선스

Private / 프로젝트 소유자 기준
