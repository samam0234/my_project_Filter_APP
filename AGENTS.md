# 컷앤킵 — 프로젝트 규칙 (AGENTS.md)

Grok / Codex / 호환 에이전트가 저장소 루트에서 자동 로드하는 **프로젝트 규칙**이다.

상세 스킬: [`.agents/skills/cutnkeep/SKILL.md`](.agents/skills/cutnkeep/SKILL.md)  
요약 복제: [`.agents/AGENTS.md`](.agents/AGENTS.md)

## 한눈에

| 항목 | 규칙 |
|------|------|
| **대화 언어** | 사용자가 한국어로 말하면 **모든 응답을 한국어로만** — 작업 중 중간 안내 · 진행 상황 · 질문 · 최종 보고 모두. 다른 언어로 말해 달라는 지시가 있을 때만 바꾼다. 코드 식별자 · 명령어 · 파일 경로 · 로그 원문은 그대로 둔다 |
| 커밋 type/scope | **영어** (`feat`, `fix`, `backend` …) |
| 커밋 제목 요약 | **한국어** (`feat(tts): 음성 인식 추가`) — 영어 요약 금지 |
| 커밋 본문·바닥글 | **한국어** |
| 작업 브랜치 | `feature/*` 등 |
| 통합 브랜치 | `develop` / `main` 만 |
| 병합 | **`git merge --no-ff`** (FF 금지) |
| **병합 시점** | **브랜치 하나 끝날 때마다 병합 금지.** 사용자가 준 파트를 각 브랜치에 모두 커밋한 뒤 **전부 끝났을 때 한 번에 총 병합** |
| 커밋 기록 파일 | **`docs/branchs/commits/` 에 무조건** (`YYMMDD_HHMM_[id]_[name]_[branch].md`) — 커밋 전·후 생략 금지. `docs/commits/` 사용 금지 |
| 비전 | **YOLO26m-seg** (기본 m — 2026-10-06 s→m, `docs/plan/YOLO26M_DEFAULT.md`) |
| LLM 기본 | Ollama `gemma4:e4b` — 화면에서 `gemma4:12b` · `qwen3.8:27b` 선택 가능(`services/llm_models.py`). GPU 서버는 `LLM_PROVIDER=lora` (Qwen2.5-1.5B 어댑터) |
| 프롬프트 규격 | `backend/app/services/prompt_spec.py` — 서빙·LoRA 학습 공용. 바꾸면 LoRA 재학습 |
| 인스턴스 선택 | `backend/app/services/instance_selector.py` (위치·순서·개수·색 규칙) |
| 계정 · 접근 | `/api/v1/auth/*` · `core/access.py` — 비로그인 처리·다운로드만(저장 없음), 기록·피드백·배치는 회원 본인 것만, 콘솔 API loopback. 가입은 **이메일 인증**(일련번호, `SIGNUP_EMAIL_VERIFICATION`), 내 계정(이름·비밀번호·전체 로그아웃·탈퇴) |
| 메일 · AI 채팅 | `services/mail_templates.py`(HTML 메일) · `services/chat_agent.py` + `routers/chat.py`(프롬프트 가이드 "에이전트에게 묻기", 대화 비저장) |
| 배포 | Oracle 서버 + Cloudflare Worker(`deploy/cloudflare/`) + PC Ollama 터널(`docker-compose.pc-ollama.yml`) — 인수인계 `docs/HANDOVER.md` |
| OpenCV 위치 | `backend/app/services/image_processor.py`, `effects.py` |
| Python 의존성 | 루트 `requirements.txt` / `requirements.docker.txt` |
| 학습 구역 | `training/` (YOLO detect/seg, LoRA) — 추론과 분리 |
| 테스트 | `tests/` + `pytest` — 실행 전 `docs/plan/TESTING.md` |
| 현재 스택 스냅샷 | `docs/plan/CURRENT_STACK.md` (포트·DB·Docker·제외 항목) |

## 커밋 제목 예시

```text
feat(tts): 음성 인식 추가     ✅
feat(llm): add to engine      ❌ (요약 영어 금지)
```

상세: `docs/guidance/commit-message.md`

## 실행

- 가이드: [`RUN.md`](./RUN.md)  
- console: `cd console && npm install && npm run dev` (5174)  
- backend: Python **3.11** venv + 루트 `requirements.txt` (3.14 비권장)

## 문서 허브

[`docs/README.md`](./docs/README.md)

## 병합 시점 (절대 규칙)

- **브랜치 하나(작업 하나)를 끝낼 때마다 `develop` / `main` 에 병합하지 않는다.**
  브랜치에서는 **커밋 + 커밋 기록(md)** 까지만 한다.
- 사용자가 준 **파트 작업을 각 브랜치에 모두 커밋한 뒤, 전부 끝났을 때 한 번에 총 병합**한다.
  (브랜치별 `git merge --no-ff`, 앞 브랜치 위에 쌓인 순서대로)
- "일단 병합해 두기", 파트 사이 중간 병합은 **금지**. 사용자가 시키지 않은 병합도 금지.
- 병합 기록 md 는 총 병합 때 한 번에 남긴다.
- 상세: `docs/guidance/branch-merge.md`

## 인수인계 · 현재 상태 (먼저 읽기)

**정본: [`docs/HANDOVER.md`](docs/HANDOVER.md)** — 지금 운영 구성 · 접근 방법 · 명령 · 규칙 · 한계 · 함정이 모두 있다. 작업 전에 읽는다.

- **운영 중 (2026-10-11 ~)**: Oracle Cloud 서버(HTTPS, `main`) + **Cloudflare Worker `cutnkeep-front`**(화면 + `/api` 프록시) + 서버의 AI 해석은 **운영자 PC 의 Ollama(SSH 역방향 터널, `scripts/ollama_tunnel.sh`)**. 점검: `python scripts/deploy_check.py remote <서버 주소>` (실패 0 · 경고 0)
- **기능**: 사진 · GIF · 영상 / 해석 모델 고르기 / 프롬프트 가이드(일반 가이드 + **AI 채팅**) / 내 계정 / **이메일 인증 가입(일련번호)** / HTML 메일 — 화면 · API · 설정 전체는 `docs/FEATURES.md`
- **테스트**: 백엔드 505 · 프런트 95 · 콘솔 21 (`docs/plan/TESTING.md`). 호스트 Python 에는 의존성이 없으니 venv 를 새로 만든다
- **비밀 값**(앱 비밀번호 · SSH 키 · `EDGE_SECRET` · `.env`)은 저장소 · 채팅 · 로그에 없다. 요청 · 출력 · 기록하지 말고, 사용자가 직접 입력해야 하면 스크립트(`scripts/set_smtp_local.sh` · `deploy/cloudflare/set_edge_secret.sh`)로 안내하고 멈춘다 — 우회 금지
- **사용자 지시를 정확히**(방법을 지정하면 그대로), 사용자 PC 의 실행 중 서버를 죽이지 않고, 만든 임시 계정 · 파일 · 컨테이너는 정리하고, 확인하지 않은 것을 "된다"고 말하지 않는다
- **병합**: 파트가 모두 끝난 뒤 사용자가 시킬 때만, 순서는 사용자 지시(보통 develop → main → push → 서버 배포). 서버 갱신은 `up -d --build backend frontend caddy ollama-bridge` 처럼 **서비스를 지정**(전체 `up` 은 adminer 를 띄운다)
