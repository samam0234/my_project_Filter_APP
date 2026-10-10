# guidance — 기능 · 실행 가이드

개발자/운영자가 기능을 **따라 실행**할 수 있게 정리한다.

## 문서 목록

| 파일 | 설명 |
|------|------|
| [commit-message.md](./commit-message.md) | **커밋 제목 영어 / 본문·바닥글 한국어** |
| [branch-merge.md](./branch-merge.md) | **작업은 feature, 일자 병합은 develop/main만 — 병합은 전체 파트가 끝난 뒤 한 번에 (브랜치마다 병합 금지)** |
| [getting-started.md](./getting-started.md) | 로컬 전체 기동 |
| [api-usage.md](./api-usage.md) | 주요 API 사용 |
| [console-admin.md](./console-admin.md) | 운영 콘솔 사용법 |
| [user-frontend.md](./user-frontend.md) | 사용자 앱 사용법 |
| [https-deploy.md](./https-deploy.md) | **HTTPS 로 공개하기** — Caddy 자동 인증서, 도메인 · DNS · 포트 |
| [gpu-deploy.md](./gpu-deploy.md) | **GPU 서버(CUDA)로 띄우기** — docker-compose.gpu.yml, 문장 해석 LoRA · 세그 GPU, 모델 옮기기 · 점검 |
| [legal.md](./legal.md) | 개인정보 처리방침 · 이용약관 — 운영자 정보 채우기, 실제 동작과의 대응표 |
| [security.md](./security.md) | **배포 전 보안·운영 점검표** — 설정 · 포트 · 보안 헤더 · 업로드 방어 · 자동 정리 · DB 백업 · 개인정보 |
| [auth.md](./auth.md) | 로그인 · 회원가입 · 아이디/비밀번호 찾기 · 보안 · SMTP |
| [docker-run.md](./docker-run.md) | cut_and_keep Compose 가이드 |
| [learning-loop.md](learning-loop.md) | 새 학습 내용이 RAG · LangChain · LangGraph · LoRA · 세그 모델로 흘러 들어가는 경로, 새 어휘 추가 절차 |
| [llm-and-vision.md](./llm-and-vision.md) | Ollama E4B · yolo26m-seg · OpenAI/Gemini |

테스트 실행: [`../plan/TESTING.md`](../plan/TESTING.md), [`../../tests/README.md`](../../tests/README.md)


## 작성 규칙

- 전제 조건 → 명령 → 기대 결과 순서
- 포트/환경변수는 표로 정리
