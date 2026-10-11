# 인수인계 — 컷앤킵 현재 상태와 운영법 (2026-10-12)

> 이 문서는 **새 에이전트(Claude · Codex · Cursor · Gemini · Copilot · Grok …)와 새 담당자**가 이 문서 하나로 지금 상태를 이해하고 이어서 일할 수 있게 쓴다.
> 규칙은 [`../AGENTS.md`](../AGENTS.md) · [`../.agents/skills/cutnkeep/SKILL.md`](../.agents/skills/cutnkeep/SKILL.md), 기능 전체는 [FEATURES.md](./FEATURES.md), 포트 · DB 스냅샷은 [plan/CURRENT_STACK.md](./plan/CURRENT_STACK.md).
> **비밀 값(비밀번호 · 키 · 토큰)은 이 문서에도, 저장소 어디에도 없다.** 아래 "접근 방법"을 읽고 사용자에게서 받는다.

## 1. 한눈에

컷앤킵은 사진 · GIF · 짧은 영상을 올리고 **한 문장**("강아지만 남기고 배경 제거")으로 대상만 남기거나 지우는 서비스다.
FastAPI 백엔드 + React 사용자 앱 + 운영 콘솔 + MariaDB. 2026-10-11 에 **실서버 배포를 마쳤고** 지금 공개 운영 중이다.

| 영역 | 상태 |
|------|------|
| 핵심 기능 (사진 · GIF · 영상, 위치 · 크기 · 순서 · 개수 · 색 선택, LaMa 지우기, 영상 추적) | ✅ 완성 |
| 해석 모델 고르기 (Ollama e4b · 12b · qwen3.8:27b) · 프롬프트 가이드 + **AI 채팅(에이전트에게 묻기)** | ✅ |
| 계정: 내 계정 · **이메일 인증 가입(일련번호)** · HTML 메일 · 아이디/비밀번호 찾기 · 탈퇴 | ✅ |
| 배포: Oracle Cloud 서버(HTTPS) + **Cloudflare Worker** 화면 + **PC 의 Ollama 를 SSH 터널로** | ✅ 동작 중 (한계는 6절) |
| 테스트 | 백엔드 505 · 프런트 95 · 콘솔 21 통과, 서버 `deploy_check remote` 실패 0 · 경고 0 |

## 2. 운영 중인 것 (실제 구성)

```text
사용자 ─▶ Cloudflare Worker(cutnkeep-front) ─ 화면(정적) / /api·/health 프록시 ─┐
사용자 ─▶ https://168-110-17-193.sslip.io ─────────────────────────────────────┤
                                       Caddy(HTTPS) ─▶ nginx(frontend) ─▶ backend ─▶ MariaDB · Redis
                                                                           └▶ ollama-bridge(172.18.0.1:11434)
                                                                                 ▲ SSH 역방향 터널(PC 가 연결, 서버 loopback 11435)
                                                                  운영자 PC 의 Ollama(11434): gemma4:e4b · gemma4:12b · qwen3.8:27b
```

| 구성 | 값 · 위치 |
|------|-----------|
| 서버 | Oracle Cloud A1.Flex(ARM 4 OCPU · 24GB · Ubuntu 24.04), 저장소 `~/cutnkeep`, **브랜치 `main`**, 사용자 `ubuntu` |
| 주소 | `https://168-110-17-193.sslip.io` (무료 와일드카드 DNS + Let's Encrypt). 자체 도메인은 아직 없다 |
| 화면(Cloudflare) | Worker `cutnkeep-front` — `https://cutnkeep-front.limjinheng0120.workers.dev` (소스 [`../deploy/cloudflare/`](../deploy/cloudflare/)). 같은 Cloudflare 계정의 `vidshare-front` · `vidshare-console` 은 **이 프로젝트가 아니다 — 건드리지 않는다** |
| 컴포즈 | `docker-compose.yml` + `docker-compose.https.yml` + `docker-compose.pc-ollama.yml` |
| 서버 `.env` 핵심 | `APP_ENV=production` · `LLM_PROVIDER=ollama` · `LLM_FALLBACK=heuristic` · `DOCKER_LLM_BASE_URL=http://172.18.0.1:11434` · `CORS_ORIGINS`(서버 + Worker 주소) · `CONSOLE_ADMINS` · `CONSOLE_REQUIRE_LOGIN=true` · `EDGE_SECRET` · `SMTP_*`(Gmail 앱 비밀번호) · `OPERATOR_*` |
| 방화벽 | OCI 보안 목록 80 · 443 + 서버 iptables(22 · 80 · 443 허용, docker 대역 `172.18.0.0/16` → 11434 허용, `netfilter-persistent` 로 저장) |
| 운영자 계정 | `while496` (`CONSOLE_ADMINS`). 내 계정에서 스스로 탈퇴 불가. 운영 콘솔은 서버에 올라가 있지 않다(관리자 PC 에서 띄워 서버 API 로) |
| 메일 | Gmail SMTP — 가입 인증 · 아이디 찾기 · 비밀번호 재설정. 받는 주소는 어떤 메일이든 된다 |
| 백업 | `data/mariaDB_backups/` 매일 · 7일 — **같은 서버 디스크뿐**(서버 밖 사본 없음) |

## 3. 접근 방법 (비밀은 사용자가 준다)

| 하는 일 | 방법 |
|---------|------|
| 서버 SSH | 개인키 **파일 경로**를 사용자에게 받는다 (`CNK_SSH_KEY`). 키 **내용은 절대 요청 · 출력 · 기록하지 않는다**. Windows PowerShell 은 키 ACL 때문에 막히면 Git Bash 의 ssh 를 쓴다 |
| 서버 `.env` | 서버에만 있다. 값을 읽어 채팅 · 저장소로 옮기지 않는다 (키 이름만 확인) |
| SMTP 앱 비밀번호 | 사용자가 서버에서 `~/set_smtp.sh`(저장소 밖)로 직접 입력했다. 이 PC 는 `bash scripts/set_smtp_local.sh` |
| `EDGE_SECRET` | `bash deploy/cloudflare/set_edge_secret.sh` — 서버 `.env` 와 Worker secret 에 같은 값을 숨겨 저장. **비밀 값을 저장소 · 서버 · Worker 에 직접 쓰는 명령은 권한 시스템이 거부한다 — 사용자가 스크립트를 직접 실행하게 한다** |
| Cloudflare | `npx wrangler login`(OAuth)이 이미 되어 있다. 배포: `cd deploy/cloudflare && npx wrangler deploy` |
| PC Ollama 터널 | `CNK_SSH_KEY=… CNK_SSH_HOST=ubuntu@<서버IP> bash scripts/ollama_tunnel.sh` — **이 창이 열려 있어야** 서버의 AI 해석 · 채팅이 동작한다 (끊기면 5초마다 재연결) |

## 4. 자주 하는 작업 (명령)

**서버 갱신** (main 이 최신일 때)
```bash
# 서버에서
cd ~/cutnkeep && git checkout main && git pull --ff-only origin main      # 서버에만 있는 파일이 충돌하면 먼저 지운다
DC='docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.pc-ollama.yml'
$DC up -d --build backend frontend caddy ollama-bridge                   # 서비스를 지정한다 — 전체 up 은 adminer(개발 도구)까지 띄운다
$DC logs --no-log-prefix --since 10m backend | grep -E '메일|signup|Error'
```
```bash
# Cloudflare 화면 (운영자 표시값은 서버 .env 의 OPERATOR_* 와 같게)
cd frontend && VITE_OPERATOR_NAME="컷앤킵 운영자" VITE_OPERATOR_EMAIL="<문의 메일>" VITE_POLICY_DATE="2026-10-11" npm run build
cd ../deploy/cloudflare && npx wrangler deploy
python scripts/deploy_check.py remote https://168-110-17-193.sslip.io    # 실패 0 · 경고 0 이어야 한다
```
배포 후 확인: 서버와 Worker 의 화면 번들 이름(`assets/index-*.js`)이 같은지, `/health` 200, `/api/v1/llm/models` 가 `enabled/reachable: true`.

**테스트** (venv 를 새로 만든다 — 호스트 Python 에는 의존성이 없다)
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.docker.txt -r tests/requirements-test.txt
.venv/Scripts/python -m pytest tests          # 505 passed
cd frontend && npx tsc --noEmit && npx vitest run   # 95 passed
cd ../console && npx vitest run                     # 21 passed
```
개인 `.env` 의 값(SMTP 등)에 테스트가 영향받지 않게 `Settings(...)` 에 값을 직접 넣는다 (한 번 깨진 적이 있다).

**테스트용 계정을 만들었다면 반드시 지운다** — 서버 컨테이너에서:
```python
user_admin.delete_user(db, ldb, user_id, confirm=username, actor_username="agent-cleanup")   # 사용자 삭제는 이 함수만
```
공개 API 로 가입한 임시 계정은 `DELETE /auth/me` (비밀번호 + 아이디)로도 지울 수 있다. 사용자 계정 · 학습 샘플은 건드리지 않는다.

## 5. 에이전트가 지켜야 할 것 (사용자와 합의된 규칙 + 겪은 일)

1. **한국어로만** 응답한다 (중간 안내 · 질문 · 보고 모두). 코드 · 명령 · 경로 · 로그는 원문 그대로.
2. **커밋**: type/scope 영어, 제목 요약 · 본문 · 바닥글 한국어. 커밋마다 `docs/branchs/commits/` 에 기록 md (템플릿 `docs/branchs/TEMPLATE.md`)를 같은 브랜치에 커밋한다.
3. **병합**: 작업은 `feature/*`. **파트가 모두 끝난 뒤 한 번에**, 사용자가 시킬 때만 `develop` → `main` (`--no-ff`, 쌓인 순서, 병합 기록 md). 사용자 지시 없는 병합 · force push 금지. 사용자가 "develop 병합 → main 병합 → push → 서버 배포"로 순서를 주면 그대로 한다.
4. **비밀 · 개인정보**: `.env` 를 커밋하지 않는다. 키 · 비밀번호 · 토큰을 요청 · 출력 · 기록하지 않는다. 사용자가 직접 입력해야 하는 건 스크립트로 안내하고 멈춘다 (우회 금지).
5. **지시를 정확히**: "다운로드 하지 말라"처럼 방법을 지정하면 그 방법을 따른다 (서버에 모델을 받다가 지적받아 정리한 적이 있다). 사용자 PC 의 실행 중 서버(예: 호스트 uvicorn)를 죽이지 않는다 — Docker 는 `BACKEND_PORT=8001` 로 피한다.
6. **사실대로 보고**: 실패 · 건너뜀 · 미확인(예: 실제 메일함 확인)을 숨기지 않는다. "된다"는 직접 실행해서 확인한 것만 말한다.
7. 사용자 학습 샘플 · 계정을 건드리지 않고, 만든 임시 계정 · 파일 · 컨테이너는 정리한다.

## 6. 알려진 한계 · 남은 일 (우선순위 순)

| # | 내용 | 비고 |
|---|------|------|
| 1 | **PC 의존**: 서버 AI 해석 · 채팅은 PC 의 Ollama 터널이 켜져 있어야 한다. 꺼지면 키워드 파서로 떨어진다(서비스는 계속) | 근본 해결 = GPU 서버(`docker-compose.gpu.yml`, [gpu-deploy.md](./guidance/gpu-deploy.md)) |
| 2 | **Cloudflare 100초 제한**: 27b · 모델 교체 직후 12b · 긴 영상 · GIF 는 Worker 주소에서 524. 서버 직접 주소는 300초 | 화면이 안내만 한다 |
| 3 | 운영자 **실명** 미입력 (개인정보 처리방침 `OPERATOR_NAME` = "컷앤킵 운영자"), **자체 도메인** 없음 | 사용자만 줄 수 있는 정보 |
| 4 | **서버 밖 백업** 없음 | 같은 디스크 |
| 5 | 로컬 개발 서버는 SMTP 미설정이면 메일이 로그에만 남는다 → `bash scripts/set_smtp_local.sh` | [repeater/local-mail-not-sent.md](./repeater/local-mail-not-sent.md) |
| 6 | 운영 콘솔 공개(접근 제한 필요) · 기존 회원 이메일 재인증 · 이메일 변경 · AI 채팅 스트리밍 | 후속 |
| 7 | 미검증: 실제 메일함에서 가입 인증 버튼 클릭, 모바일 실기기, 부하 · 동시 접속 | |

## 7. 겪은 함정 (재발 방지)

- **backend 가 다시 만들어지면 nginx 가 옛 IP 로 502** → `resolver` 로 해결 ([repeater/nginx-backend-502.md](./repeater/nginx-backend-502.md)). 진단: 서버 직접 주소 502 면 서버, 직접은 되고 Worker 만 502 면 Worker/`EDGE_SECRET`.
- 서버에서 **전체 `up -d --build`** 는 adminer 를 띄운다 → 서비스를 지정한다.
- 서버 `git pull` 전에 서버에만 있는 파일(예: 옛 오버레이 복사본)을 지운다 (충돌).
- **Gmail `+별칭`** 주소(`name+x@gmail.com`)는 전부 같은 받은편지함으로 온다 — 테스트 메일이 한 곳에 모여 "고정으로 간다"고 오해하기 쉽다.
- 로컬 개발 서버와 서버는 **회원 DB 가 따로**다 (운영자 `while496` 은 서버에만 있다).
- 호스트 백엔드와 Docker 백엔드가 같은 SQLite 를 공유하면 손상된 적이 있다 (DB 파일 분리).
- Windows 셸에서 한글 JSON 을 `curl -d` 로 직접 보내면 깨진다 → UTF-8 파일 `--data-binary @file`.
- 임시 가상환경 · 내려받은 모델 · 스크린샷은 저장소 밖 임시 폴더에 두고 끝나면 지운다.

## 8. 코드 지도 (최근 추가분)

| 기능 | 백엔드 | 프런트 | 테스트 |
|------|--------|--------|--------|
| 이메일 인증 가입 | `routers/auth.py`(signup/start·verify·resend) · `services/auth_service.py` · `models/user.py`(SignupPending) · `core/passwords.py`(일련번호) | `pages/auth/SignupPage` · `SignupVerifyPage` | `tests/unit/test_signup_verify.py` |
| 내 계정 | `PATCH/DELETE /auth/me` · `password/change` · `logout-all` | `pages/AccountPage` · `components/account/HistoryPanel` · `components/layout/AppLayout`(프로필 메뉴) | `test_auth.py` · `AccountSettings.test.tsx` |
| HTML 메일 | `services/mail_templates.py` · `services/mailer.py` · `core/deps.site_url` | — | `test_mail_templates.py` |
| AI 채팅 | `routers/chat.py` · `services/chat_agent.py`(시스템 프롬프트) · `schemas/chat.py` | `components/chat/AgentChat` · `store/useChatStore` · `pages/GuidePage`(탭) | `test_chat.py` · `GuidePage.test.tsx` |
| 모델 고르기 | `services/llm_models.py` · `routers/llm.py` | `components/common/ModelSelect` · `store/useLlmModelStore` | `test_llm_models.py` |
| Cloudflare | — | `deploy/cloudflare/{worker.js,wrangler.jsonc,set_edge_secret.sh}` · `frontend/public/_headers` | (배포 후 `deploy_check`) |
| PC Ollama 터널 | `docker-compose.pc-ollama.yml` | `scripts/ollama_tunnel.sh` | — |

설정은 `backend/app/core/config.py` ↔ `.env.example` ↔ 문서가 **모두** 있어야 한다 — `tests/structure/test_docs_coverage.py` 가 엔드포인트 · 설정 · 화면 경로의 문서 누락을 잡는다.

## 9. 새 기능을 넣을 때 체크

1. `feature/*` 브랜치 → 구현 + 테스트 (`pytest` · `vitest` · `tsc`)
2. 문서: API_DOCUMENTATION · FEATURES · user-frontend(화면) · frontend/backend README · `.env.example`(설정) · 필요하면 security · legal(개인정보) · 이 문서
3. 커밋 + 커밋 기록 md → (사용자 지시 시) develop → main 병합, push
4. 배포는 위 4절 순서, 끝나면 `deploy_check remote` 와 새 기능을 **실제로 한 번 호출**해 확인
