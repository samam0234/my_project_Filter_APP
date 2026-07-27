# Cut & Keep · Documentation Hub

프로젝트 문서 진입점입니다.

## 폴더 맵

| 폴더 | 용도 |
|------|------|
| [plan/](./plan/) | 초기 기획·로직·DB·배포 계획 (기존) |
| [Architecture/](./Architecture/) | 시스템·계층·데이터 흐름 아키텍처 |
| [branchs/](./branchs/) | 브랜치·커밋 기록 (템플릿 필수) |
| [find_debug/](./find_debug/) | 작업/실행 디버깅 일일 기록 |
| [guidance/](./guidance/) | 기능·실행 가이드 |
| [trainings/](./trainings/) | 학습·연구 정리 |
| [repeater/](./repeater/) | 서버 연결·인프라 장애와 해결 |
| [vaildates/](./vaildates/) | 검증·체크리스트 |
| [web_management/](./web_management/) | 배포 전/배포 시 웹 관리 기록 |

## 앱 구성

| 경로 | 역할 | 포트 |
|------|------|------|
| `frontend/` | 사용자 필터 앱 | 5173 |
| `console/` | **운영 관리자 콘솔** | 5174 |
| `backend/` | FastAPI | 8000 |

## 빠른 링크

- **실행 · 서버:** [../RUN.md](../RUN.md)
- **AI 모델 전략:** [plan/AI_MODEL_STRATEGY.md](./plan/AI_MODEL_STRATEGY.md)
- **테스트 전략:** [plan/TESTING.md](./plan/TESTING.md) · [../tests/README.md](../tests/README.md)
- API: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- 배포: [DEPLOYMENT.md](./DEPLOYMENT.md)
- 워크플로: [WORKFLOW.md](./WORKFLOW.md)
- **커밋 메시지 규칙:** [guidance/commit-message.md](./guidance/commit-message.md)
- **브랜치 병합 규칙:** [guidance/branch-merge.md](./guidance/branch-merge.md)
- 커밋 기록 템플릿: [branchs/TEMPLATE.md](./branchs/TEMPLATE.md)

- 에이전트 스킬: [../.agents/skills/cutnkeep/SKILL.md](../.agents/skills/cutnkeep/SKILL.md) · [../AGENTS.md](../AGENTS.md)

