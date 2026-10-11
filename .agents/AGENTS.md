# 컷앤킵 에이전트 지침

**원본 스킬 경로:** `.agents/skills/cutnkeep/SKILL.md`  
**루트 규칙:** `AGENTS.md` (Grok 프로젝트 규칙 자동 로드)

## 대화 언어 (필수)

사용자가 한국어로 말하면 **모든 응답을 한국어로만** — 작업 중 중간 안내 · 진행 상황 · 질문 · 최종 보고 모두. 다른 언어로 말해 달라는 지시가 있을 때만 바꾼다. 코드 식별자 · 명령어 · 파일 경로 · 로그 원문은 그대로 둔다.

## 자주 여는 문서

1. `.agents/skills/cutnkeep/SKILL.md`  
2. `docs/guidance/commit-message.md`  
3. `docs/guidance/branch-merge.md`  
4. `docs/branchs/TEMPLATE.md`  
5. 백엔드 작업 시 `docs/plan/LOGIC_STRUCTURE.md`, `DATABASE.md`, `AI_MODEL_STRATEGY.md`

## 커밋

```text
type(scope): 한국어 요약

한국어 본문

한국어 바닥글
```

- type/scope 만 영어  
- 제목 요약은 **한글** (`feat(tts): 음성 인식 추가`)  
- 영어 요약 금지 (`feat(llm): add to engine` ❌)  
- **커밋 기록 필수:** `docs/branchs/commits/YYMMDD_HHMM_….md`  
  - 커밋 전·후 **무조건** 작성 · `docs/commits/` 금지  
  - 템플릿: `docs/branchs/TEMPLATE.md`

## 브랜치

- 작업: `feature/*`  
- develop/main 병합: **`git merge --no-ff` 필수**  
- FF 만 쓰면 Git Graph 가 일자로 보임  

## 스택

- backend FastAPI · frontend :5173 · console :5174  
- Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
- Docker: `-p cut_and_keep`, backend build context = 저장소 루트  

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
