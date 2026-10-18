# docs — 컷앤킵 문서 허브

> 컷앤킵의 모든 문서가 여기서 시작한다. **처음이라면 [HANDOVER.md](./HANDOVER.md) 한 장부터** 읽는다.

문서는 "지금 상태"를 적는 정본과, 그 정본을 뒷받침하는 계획 · 가이드 · 검증 · 기록으로 나뉜다.
정본끼리 내용이 다르면 **HANDOVER → FEATURES → plan/CURRENT_STACK** 순서로 믿고, 어긋난 쪽을 고친다.

---

## 1. 처음 읽는 순서

| 순서 | 문서 | 얻는 것 |
|------|------|---------|
| 1 | [HANDOVER.md](./HANDOVER.md) | **인수인계 정본** — 운영 구성 · 접근 방법 · 자주 하는 명령 · 에이전트 규칙 · 한계 · 겪은 함정 |
| 2 | [FEATURES.md](./FEATURES.md) | 전체 기능 목록 — 화면 · API · 설정 · 코드 · 문서가 한 표에 |
| 3 | [plan/CURRENT_STACK.md](./plan/CURRENT_STACK.md) | 지금 포트 · DB · Docker · 모델 스냅샷 |
| 4 | [../RUN.md](../RUN.md) | 로컬 3터미널 + Docker 실행 |
| 5 | [../README.md](../README.md) | 프로젝트 소개 (문제 · 구조 · 기술 · 숫자) |

---

## 2. 상황별로 무엇을 읽나

| 하려는 일 | 문서 |
|-----------|------|
| 로컬에서 띄우기 | [../RUN.md](../RUN.md) · [guidance/getting-started.md](./guidance/getting-started.md) · [guidance/docker-run.md](./guidance/docker-run.md) |
| 운영 서버 갱신 | [HANDOVER.md 4절](./HANDOVER.md) · [DEPLOYMENT.md](./DEPLOYMENT.md) |
| 처음부터 공개 배포 | [DEPLOYMENT.md](./DEPLOYMENT.md) → [guidance/https-deploy.md](./guidance/https-deploy.md) → [guidance/cloudflare-deploy.md](./guidance/cloudflare-deploy.md) → [guidance/ollama-server.md](./guidance/ollama-server.md) |
| GPU 서버로 옮기기 | [guidance/gpu-deploy.md](./guidance/gpu-deploy.md) |
| 배포 전 보안 점검 | [guidance/security.md](./guidance/security.md) · [web_management/pre-deploy.md](./web_management/pre-deploy.md) |
| API 붙이기 | [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) · [guidance/api-usage.md](./guidance/api-usage.md) |
| 처리 흐름 이해 | [WORKFLOW.md](./WORKFLOW.md) (LangGraph) · [plan/LOGIC_STRUCTURE.md](./plan/LOGIC_STRUCTURE.md) · [Architecture/](./Architecture/README.md) |
| 문장 해석 · 모델 바꾸기 | [guidance/llm-and-vision.md](./guidance/llm-and-vision.md) · [plan/AI_MODEL_STRATEGY.md](./plan/AI_MODEL_STRATEGY.md) |
| 학습 데이터가 어디로 가나 | [guidance/learning-loop.md](./guidance/learning-loop.md) · [../training/README.md](../training/README.md) |
| 계정 · 메일 | [guidance/auth.md](./guidance/auth.md) |
| 처리방침 · 약관 | [guidance/legal.md](./guidance/legal.md) |
| DB 구조 | [plan/DATABASE.md](./plan/DATABASE.md) · [../docker/mariadb/README.md](../docker/mariadb/README.md) |
| 테스트 | [plan/TESTING.md](./plan/TESTING.md) · [../tests/README.md](../tests/README.md) |
| 숫자의 근거 찾기 | [vaildates/README.md](./vaildates/README.md) |
| 같은 장애가 또 났을 때 | [repeater/](./repeater/README.md) · [find_debug/](./find_debug/README.md) |
| 커밋 · 브랜치 · 병합 | [guidance/commit-message.md](./guidance/commit-message.md) · [guidance/branch-merge.md](./guidance/branch-merge.md) · [branchs/](./branchs/README.md) |

---

## 3. 폴더 지도

| 폴더 | 무엇이 있나 |
|------|-------------|
| [plan/](#plan--계획과-설계) | 설계 · 계획 · 현재 스택 스냅샷 · 모델 전략 · DB · 테스트 전략 |
| [guidance/](./guidance/README.md) | 기능 · 실행 · 배포 가이드 (따라 하는 문서) |
| [Architecture/](./Architecture/README.md) | 시스템 · 계층 · 데이터 흐름 · Docker 토폴로지 |
| [vaildates/](./vaildates/README.md) | 검증 · 실험 결과 — 문서에 적힌 수치의 근거 |
| [repeater/](./repeater/README.md) | 재발할 수 있는 서버 연결 · 인프라 장애와 해결 |
| [find_debug/](./find_debug/README.md) | 날짜별 디버깅 기록 |
| [trainings/](./trainings/README.md) | 배운 것 정리 (왜 이렇게 했는지) |
| [web_management/](./web_management/README.md) | 배포 전 · 배포 · 배포 후 점검과 포트 목록 |
| [branchs/](./branchs/README.md) | 브랜치 지도 · **커밋마다 남기는 기록**(`branchs/commits/`) · 템플릿 |

### 맨 위 문서

| 문서 | 내용 |
|------|------|
| [HANDOVER.md](./HANDOVER.md) | 인수인계 정본 |
| [FEATURES.md](./FEATURES.md) | 전체 기능 목록 |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | 모든 API 엔드포인트 (문서 등록 검사가 확인한다) |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 공개 서버에 올리는 순서 · 실제 배포 기록 |
| [WORKFLOW.md](./WORKFLOW.md) | LangGraph 처리 흐름 |

### plan — 계획과 설계

| 문서 | 내용 |
|------|------|
| [CURRENT_STACK.md](./plan/CURRENT_STACK.md) | **지금** 포트 · DB · Docker · 모델 스냅샷 |
| [AI_MODEL_STRATEGY.md](./plan/AI_MODEL_STRATEGY.md) | YOLO26m-seg · Ollama E4B · 클라우드 LLM 전략 |
| [LOGIC_STRUCTURE.md](./plan/LOGIC_STRUCTURE.md) | 통합 로직 구조 · 피드백 → LoRA 루프 |
| [DATABASE.md](./plan/DATABASE.md) | 데이터베이스 설계 (SQLite / MariaDB, 서비스 · 학습 DB) |
| [PROJECT_STRUCTURE.md](./plan/PROJECT_STRUCTURE.md) | 폴더 · 모듈 구조 기획 |
| [TESTING.md](./plan/TESTING.md) | 테스트 전략 |
| [ONNX_INFERENCE.md](./plan/ONNX_INFERENCE.md) | torch · ultralytics 없이 ONNX 세그 추론 |
| [YOLO26M_DEFAULT.md](./plan/YOLO26M_DEFAULT.md) · [YOLO26S_DEFAULT.md](./plan/YOLO26S_DEFAULT.md) | 비전 기본 모델 전환 기록 (n → s → m) |
| [HARDCODING_ZONES.md](./plan/HARDCODING_ZONES.md) | 하드코딩 구간 · 완성도 부족분 지도 |
| [LOGIC_AND_GIT_BRANCH_STRATEGY.md](./plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md) | 실행 규칙 + Git 브랜치 전략 |
| [DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md](./plan/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md) | 환경 · 실행 · 배포 (초기 가이드) |
| `DEVELOPMENT_PLAN.docx` | 초기 개발 계획 (Word) |

---

## 4. 앱 구성

| 경로 | 역할 | 포트 |
|------|------|------|
| `frontend/` | 사용자 앱 | 5173 (Docker 80) |
| `console/` | **운영 관리자 콘솔** | 5174 |
| `backend/` | FastAPI | 8000 |
| `Portfolio/site/` | 설명 사이트 (제품 아님, Next.js) | 5190 |
| `Portfolio/ai/` | 설명 사이트의 안내 챗 (Flask) | 5055 |

설명 사이트: [../Portfolio/README.md](../Portfolio/README.md)

---

## 5. 문서를 쓰는 규칙

- **사실만 적는다.** 확인하지 않은 것을 "된다"고 적지 않고, 미검증은 미검증이라고 적는다.
- **수치에는 근거를 붙인다.** 실험 결과는 `vaildates/`에 두고 다른 문서는 그 문서를 링크한다.
- **기능이 바뀌면 문서도 같이 바꾼다.** 새 API · 설정 · 화면이 문서에 빠지면 `tests/structure/test_docs_coverage.py`가 실패한다.
- **보관 기간을 바꾸면** 처리방침 · 화면 문구도 같은 커밋에서 바꾼다 (어긋난 적이 있다).
- **비밀 값은 적지 않는다.** 키 · 비밀번호 · 토큰 · `.env` 값은 어떤 문서에도 없다. 키 이름만 적는다.
- **커밋 기록은 `branchs/commits/`에만** 남긴다 (`docs/commits/` 금지). 템플릿: [branchs/TEMPLATE.md](./branchs/TEMPLATE.md)
- 다이어그램은 ASCII 또는 mermaid를 쓴다.

에이전트 규칙: [../AGENTS.md](../AGENTS.md) · [../.agents/skills/cutnkeep/SKILL.md](../.agents/skills/cutnkeep/SKILL.md)
