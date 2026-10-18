# guidance — 기능 · 실행 · 배포 가이드

> 개발자 · 운영자가 **따라 하면 되는** 문서. 전제 조건 → 명령 → 기대 결과 순서로 쓴다.

설계 이유나 계획은 [`../plan/`](../README.md#plan--계획과-설계)에, 검증 수치는 [`../vaildates/`](../vaildates/README.md)에 있다. 이 폴더는 "어떻게 하나"를 다룬다.

---

## 1. 무엇부터 읽나

| 상황 | 순서 |
|------|------|
| 처음 로컬에서 띄운다 | [getting-started.md](./getting-started.md) → [docker-run.md](./docker-run.md) |
| 사용자 앱을 이해한다 | [user-frontend.md](./user-frontend.md) → [auth.md](./auth.md) |
| 운영 콘솔을 쓴다 | [console-admin.md](./console-admin.md) → [learning-loop.md](./learning-loop.md) |
| API를 붙인다 | [api-usage.md](./api-usage.md) (+ [`../API_DOCUMENTATION.md`](../API_DOCUMENTATION.md)) |
| 문장 해석 · 모델을 바꾼다 | [llm-and-vision.md](./llm-and-vision.md) → [learning-loop.md](./learning-loop.md) |
| 공개 서버에 올린다 | [security.md](./security.md) → [https-deploy.md](./https-deploy.md) → [cloudflare-deploy.md](./cloudflare-deploy.md) → [ollama-server.md](./ollama-server.md) → [legal.md](./legal.md) |
| GPU 서버로 옮긴다 | [gpu-deploy.md](./gpu-deploy.md) |
| 커밋 · 병합한다 | [commit-message.md](./commit-message.md) → [branch-merge.md](./branch-merge.md) |

---

## 2. 문서 목록

### 실행 · 사용

| 파일 | 설명 |
|------|------|
| [getting-started.md](./getting-started.md) | 로컬 전체 기동 — 백엔드 · 사용자 앱 · 콘솔 |
| [docker-run.md](./docker-run.md) | `cut_and_keep` Compose 가이드 |
| [user-frontend.md](./user-frontend.md) | 사용자 앱 사용 흐름 — 모든 화면 경로 (문서 등록 검사 대상) |
| [console-admin.md](./console-admin.md) | 운영 콘솔 사용법 · 접근 규칙 · 학습 데이터 검수 |
| [api-usage.md](./api-usage.md) | 주요 API 호출 예 |
| [auth.md](./auth.md) | 로그인 · 회원가입(**이메일 인증**) · **내 계정** · 아이디 / 비밀번호 찾기 · **HTML 메일** · 보안 · SMTP(서버 · 로컬) |

### AI · 학습

| 파일 | 설명 |
|------|------|
| [llm-and-vision.md](./llm-and-vision.md) | 프롬프트 규격(selector · remove_object) · Ollama E4B · yolo26m-seg · RAG · Chroma · LoRA · OpenAI/Gemini |
| [learning-loop.md](./learning-loop.md) | 새 학습 내용이 RAG · LangChain · LangGraph · LoRA · 세그 모델로 흘러 들어가는 경로, 새 어휘 추가 절차 |

### 배포 · 운영

| 파일 | 설명 |
|------|------|
| [security.md](./security.md) | **배포 전 보안 · 운영 점검표** — 설정 · 포트 · 보안 헤더 · 업로드 방어 · 자동 정리 · DB 백업 · 개인정보 |
| [https-deploy.md](./https-deploy.md) | **HTTPS로 공개하기** — Caddy 자동 인증서, 도메인 · DNS · 포트 |
| [cloudflare-deploy.md](./cloudflare-deploy.md) | **화면을 Cloudflare Worker로** — 정적 화면 + `/api` 프록시, `EDGE_SECRET`, 502 진단 |
| [ollama-server.md](./ollama-server.md) | **서버가 내 PC의 Ollama 쓰기** — SSH 역방향 터널 · 다리 컨테이너 · 방화벽 · 측정값 |
| [gpu-deploy.md](./gpu-deploy.md) | **GPU 서버(CUDA)** — `docker-compose.gpu.yml`, 문장 해석 LoRA · 세그 GPU, 모델 옮기기 · 점검 |
| [legal.md](./legal.md) | 개인정보 처리방침 · 이용약관 — 운영자 정보 채우기, 실제 동작과의 대응표 |

### 협업 규칙

| 파일 | 설명 |
|------|------|
| [commit-message.md](./commit-message.md) | **type / scope 영어, 제목 요약 · 본문 · 바닥글 한국어** |
| [branch-merge.md](./branch-merge.md) | **작업은 `feature/*`, 통합은 `develop` / `main`만 — 병합은 파트가 모두 끝난 뒤 한 번에 (브랜치마다 병합 금지)** |

테스트 실행: [`../plan/TESTING.md`](../plan/TESTING.md) · [`../../tests/README.md`](../../tests/README.md)

---

## 3. 작성 규칙

- **전제 조건 → 명령 → 기대 결과** 순서로 쓴다. 명령은 복사해서 바로 돌릴 수 있게.
- 포트 · 환경변수는 **표로** 정리한다.
- 비밀 값은 적지 않는다. 사용자가 직접 넣어야 하는 값은 스크립트(`scripts/set_smtp_local.sh` · `deploy/cloudflare/set_edge_secret.sh`)로 안내한다.
- Windows(PowerShell)와 Git Bash가 다르면 둘 다 적는다. 한글 JSON은 `curl -d` 대신 UTF-8 파일 `--data-binary @file`.
- 기능이 바뀌면 같은 커밋에서 이 폴더를 고친다.
