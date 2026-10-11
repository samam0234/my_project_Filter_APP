# Claude — 컷앤킵

이 저장소는 공유 에이전트 규칙을 사용한다.

**주 지시:** 루트 `AGENTS.md`, `.agents/skills/cutnkeep/SKILL.md`

## 대화 언어 (필수)

- 사용자가 한국어로 말하면 **모든 응답을 한국어로만** 한다
  — 작업 중 도구 호출 사이의 중간 안내 · 진행 상황 · 질문 · 최종 보고 모두 포함
- 다른 언어로 말해 달라는 **명시적인 지시가 있을 때만** 그 언어로 바꾼다
- 코드 식별자 · 명령어 · 파일 경로 · 로그 원문 · 커밋 type/scope 는 그대로 둔다

## 커밋 메시지

- **type / scope:** 영어 (`feat`, `fix`, `backend` …)  
- **제목 요약:** **한국어** (`feat(tts): 음성 인식 추가`)  
- **본문·바닥글:** 한국어  
- 영어 요약 금지: `feat(llm): add to engine` ❌  

→ `docs/guidance/commit-message.md`

## 커밋 기록 (필수 · 예외 없음)

- **경로:** `docs/branchs/commits/` **만** (`docs/commits/` 금지)  
- **커밋 전 또는 직후 무조건** md 작성  
- 파일명: `YYMMDD_HHMM_[id]_[이름]_[브랜치].md`  
- 템플릿: `docs/branchs/TEMPLATE.md`  
- 기록 파일도 같은 브랜치에 커밋·푸시  
- 생략·나중에 하기 금지

## 브랜치

- 작업 커밋: `feature/*`  
- 일자 병합: `develop` / `main` 만  
→ `docs/guidance/branch-merge.md`
- **병합 시점 (절대 규칙):** 브랜치 하나 끝날 때마다 병합 **금지**. 사용자가 준 파트 작업을 각 브랜치에 모두 커밋한 뒤, **전부 끝났을 때 한 번에 총 병합** (브랜치별 `--no-ff`, 쌓인 순서대로). 중간 병합·사용자 지시 없는 병합 금지. 병합 기록 md 도 총 병합 때 한 번에

## 스택

- `backend/` FastAPI · `frontend/` :5173 · `console/` :5174  
- Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
- Docker: `-p cut_and_keep`  

## 인수인계 · 현재 상태 (먼저 읽기)

**정본: [`docs/HANDOVER.md`](docs/HANDOVER.md)** — 지금 운영 구성 · 접근 방법 · 명령 · 규칙 · 한계 · 함정이 모두 있다. 작업 전에 읽는다.

- **운영 중 (2026-10-11 ~)**: Oracle Cloud 서버(HTTPS, `main`) + **Cloudflare Worker `cutnkeep-front`**(화면 + `/api` 프록시) + 서버의 AI 해석은 **운영자 PC 의 Ollama(SSH 역방향 터널, `scripts/ollama_tunnel.sh`)**. 점검: `python scripts/deploy_check.py remote <서버 주소>` (실패 0 · 경고 0)
- **기능**: 사진 · GIF · 영상 / 해석 모델 고르기 / 프롬프트 가이드(일반 가이드 + **AI 채팅**) / 내 계정 / **이메일 인증 가입(일련번호)** / HTML 메일 — 화면 · API · 설정 전체는 `docs/FEATURES.md`
- **테스트**: 백엔드 505 · 프런트 95 · 콘솔 21 (`docs/plan/TESTING.md`). 호스트 Python 에는 의존성이 없으니 venv 를 새로 만든다
- **비밀 값**(앱 비밀번호 · SSH 키 · `EDGE_SECRET` · `.env`)은 저장소 · 채팅 · 로그에 없다. 요청 · 출력 · 기록하지 말고, 사용자가 직접 입력해야 하면 스크립트(`scripts/set_smtp_local.sh` · `deploy/cloudflare/set_edge_secret.sh`)로 안내하고 멈춘다 — 우회 금지
- **사용자 지시를 정확히**(방법을 지정하면 그대로), 사용자 PC 의 실행 중 서버를 죽이지 않고, 만든 임시 계정 · 파일 · 컨테이너는 정리하고, 확인하지 않은 것을 "된다"고 말하지 않는다
- **병합**: 파트가 모두 끝난 뒤 사용자가 시킬 때만, 순서는 사용자 지시(보통 develop → main → push → 서버 배포). 서버 갱신은 `up -d --build backend frontend caddy ollama-bridge` 처럼 **서비스를 지정**(전체 `up` 은 adminer 를 띄운다)
