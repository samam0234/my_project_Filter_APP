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

- **전체 기능 목록 (화면 · API · 설정 · 코드 · 문서):** [FEATURES.md](./FEATURES.md)
- **현재 스택 스냅샷 (포트·DB·Docker):** [plan/CURRENT_STACK.md](./plan/CURRENT_STACK.md)
- **실행 · 서버:** [../RUN.md](../RUN.md) · [guidance/docker-run.md](./guidance/docker-run.md)
- **AI 모델 전략:** [plan/AI_MODEL_STRATEGY.md](./plan/AI_MODEL_STRATEGY.md) · **YOLO s→m:** [plan/YOLO26M_DEFAULT.md](./plan/YOLO26M_DEFAULT.md)
- **계정 (로그인 · 회원가입 · 찾기):** [guidance/auth.md](./guidance/auth.md)
- **보안 · 배포 전 점검표:** [guidance/security.md](./guidance/security.md)
- **학습 루프 (RAG · LangChain · LangGraph · LoRA):** [guidance/learning-loop.md](./guidance/learning-loop.md)
- **검증 · 실험 결과 (수치 근거):** [vaildates/README.md](./vaildates/README.md)
- **LLM · 비전 · 프롬프트 규격:** [guidance/llm-and-vision.md](./guidance/llm-and-vision.md)
- **학습:** [../training/README.md](../training/README.md) · LoRA 평가 [../training/lora/README.md](../training/lora/README.md)
- **테스트:** [plan/TESTING.md](./plan/TESTING.md) · [../tests/README.md](../tests/README.md)
- **DB:** [plan/DATABASE.md](./plan/DATABASE.md) · [../docker/mariadb/README.md](../docker/mariadb/README.md)
- API: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **배포 순서 (운영 `.env` · HTTPS · GPU · 모델 옮기기 · 점검):** [DEPLOYMENT.md](./DEPLOYMENT.md) · [guidance/https-deploy.md](./guidance/https-deploy.md) · [guidance/gpu-deploy.md](./guidance/gpu-deploy.md) · [web_management/ports-inventory.md](./web_management/ports-inventory.md)
- **개인정보 처리방침 · 약관 운영:** [guidance/legal.md](./guidance/legal.md)
- 워크플로: [WORKFLOW.md](./WORKFLOW.md)
- **커밋 메시지:** [guidance/commit-message.md](./guidance/commit-message.md)
- **브랜치 병합:** [guidance/branch-merge.md](./guidance/branch-merge.md)
- **커밋 기록 (필수 경로):** [branchs/commits/](./branchs/commits/) · 템플릿 [branchs/TEMPLATE.md](./branchs/TEMPLATE.md)  
  → `docs/commits/` 사용 금지

- 에이전트 스킬: [../.agents/skills/cutnkeep/SKILL.md](../.agents/skills/cutnkeep/SKILL.md) · [../AGENTS.md](../AGENTS.md)

