---
name: cutnkeep
description: "컷앤킵(CutNKeep) 프로젝트 규칙. 한국어로 말하는 사용자에게는 지시가 없는 한 모든 응답(중간 안내 포함)을 한국어로. 커밋 시 docs/branchs/commits 에 md 기록 필수(docs/commits 금지), 제목 요약 한국어(type/scope 영어), feature 브랜치, develop·main --no-ff, YOLO26m-seg·Ollama E4B. 트리거: commit, branchs, commits, console, backend, cutnkeep, ollama, yolo."
---

# 컷앤킵 프로젝트 스킬

## 대화 언어 (필수)

사용자가 한국어로 말하면 **모든 응답을 한국어로만** — 작업 중 중간 안내 · 진행 상황 · 질문 · 최종 보고 모두. 다른 언어로 말해 달라는 지시가 있을 때만 바꾼다. 코드 식별자 · 명령어 · 파일 경로 · 로그 원문은 그대로 둔다.

## 프로젝트

- 이름: 컷앤킵 / Cut & Keep  
- 루트: `backend/`, `frontend/`, `console/`, `docs/`, `docker-compose.yml`  
- 현재(2026-10-12): Phase 1~3 구현 + **실서버 배포 완료** — 사진 · GIF · 영상, 해석 모델 고르기, AI 채팅, 내 계정, 이메일 인증 가입, HTML 메일, Cloudflare Worker 화면, PC Ollama 터널. 인수인계 정본 `docs/HANDOVER.md`  
- 비전: **YOLO26m-seg** (기본 m; s→m 안내 `docs/plan/YOLO26M_DEFAULT.md`)  
- LLM 기본: **Ollama gemma4:e4b** · 빠른 로컬: `lora` (Qwen2.5-1.5B 어댑터) · 고도화: OpenAI/Gemini
- 프롬프트 규격 정본: `backend/app/services/prompt_spec.py` (바꾸면 `training/lora` 재학습)
- 런타임(uploads·SQLite·서빙 모델·앱 로그)은 `backend/`, 학습 공유(feedback·pseudo·모델 원본)는 루트  
  → `docs/plan/AI_MODEL_STRATEGY.md`
- Python 의존성: **저장소 루트** `requirements.txt` / `requirements.docker.txt`

## 백엔드 아키텍처

```
routers → services/workflows → repositories → models
routers → schemas
```

- 라우터에 SQL 금지. 레포지토리에 OpenCV 금지.  
- DB: `DB_DIALECT=sqlite|mariadb` → `docs/plan/DATABASE.md`  
- OpenCV 위치: `backend/app/services/image_processor.py`, `effects.py`, `utils/image_utils.py`

## 앱

| 경로 | 역할 | 포트 |
|------|------|------|
| `frontend/` | 사용자 필터 UI | 5173 |
| `console/` | 운영 관리자 | 5174 |
| `backend/` | API | 8000 |

## Git 커밋 (필수)

| 구간 | 언어 |
|------|------|
| **type / scope** | **영어** (`feat`, `fix`, `backend` …) |
| **제목 요약** | **한국어** (`feat(tts): 음성 인식 추가`) |
| **본문** | **한국어** |
| **바닥글** | **한국어** |

### 제목 규칙

```text
feat(tts): 음성 인식 추가          ✅
feat(llm): add to engine           ❌ 요약 영어 금지
```

형식: `type(scope): <한국어 한 줄 요약>`  
상세: `docs/guidance/commit-message.md`

## 커밋 기록 (필수 · 예외 없음)

**경로 (이것만 사용):** `docs/branchs/commits/`  
**금지:** `docs/commits/` 등 다른 경로에 남기기 · 기록 생략 · “나중에” · 푸시만 하고 끝내기

에이전트는 **커밋을 하거나 하기 전에 무조건** 아래 md 를 남긴다.

```text
docs/branchs/commits/YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

| 규칙 | 내용 |
|------|------|
| 시점 | **커밋 직전(초안)** 또는 **커밋 직후(SHA 확정)** — 둘 중 하나 이상, **무조건** |
| 템플릿 | `docs/branchs/TEMPLATE.md` 준수 (한 줄 요약만 금지) |
| 후속 | 기록 파일도 **같은 브랜치에 커밋** (`docs(branchs): …`) 후 push |
| 대상 | 기능·docs·merge·chore 커밋 모두. “작다”고 생략 금지 |
| 파일명 | `YYMMDD_HHMM` + short SHA + kebab name + 브랜치(`/`→`-`) |

체크리스트 (커밋/푸시 전):

- [ ] `docs/branchs/commits/*.md` 작성했는가  
- [ ] 파일명 규칙 맞는가  
- [ ] 템플릿 섹션 채웠는가  
- [ ] 기록 파일도 git 에 올렸는가  

## 브랜치 (필수)

- 작업·커밋: `feature/*` 등에서만  
- 통합: **`develop` / `main` 만**, 병합 시 **`git merge --no-ff` (FF 금지)**  
- 가이드: `docs/guidance/branch-merge.md`

## Docker

`docker compose -p cut_and_keep ...` · Redis 호스트 포트 `6380` 주의  
backend 빌드 context = **저장소 루트** (`dockerfile: backend/Dockerfile`)

## 안전

- `.env` 시크릿 커밋 금지  
- force-push 금지 (사용자 요청 시 제외)  

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
