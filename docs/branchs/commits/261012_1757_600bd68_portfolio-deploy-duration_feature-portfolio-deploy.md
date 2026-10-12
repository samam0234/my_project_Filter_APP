# Vercel Hobby 한도에 맞게 챗 함수 시간 조정 / `600bd68c39707fc69ff7b12ef99adaa42a44f2ce`

> 브랜치: `feature/portfolio-deploy`  
> 작성일: `2026-10-12 17:57`  
> 작성자: `agent`  
> 파일명: `261012_1757_600bd68_portfolio-deploy-duration_feature-portfolio-deploy.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(portfolio): Vercel Hobby 한도에 맞게 챗 함수 시간 조정` |
| **커밋 번호 (SHA)** | `600bd68c39707fc69ff7b12ef99adaa42a44f2ce` |
| **짧은 SHA** | `600bd68` |
| **브랜치** | `feature/portfolio-deploy` |
| **부모 커밋** | `4d816a1ea0545628eb808f22b748e7e1a98e60ef` |

## 2. 주 커밋 내용

- `Portfolio/site/app/api/chat/route.ts` 의 `maxDuration` 을 600에서 300으로 낮춤
- 깊이 추론 요청의 대기 한도를 600000ms 에서 290000ms 로 낮춤 (함수 한도 안)
- `.gitignore` 에 `.vercel/`, `.env.local` 추가 (Vercel CLI 연결 정보와 로컬 토큰)

## 3. 상세 내용

### 3.1 배경 / 목적

`Portfolio/site` 를 Vercel 에 올리자 빌드는 통과했지만 배포 단계에서
`Serverless Functions must have a maxDuration between 1 and 300 for plan hobby` 로 거부됐다.

### 3.2 변경 범위

- 수정된 경로: `Portfolio/site/app/api/chat/route.ts`, `.gitignore`

### 3.3 기술 포인트

- 배포 구성
  - `Portfolio/site` → Vercel 프로젝트 `cutnkeep-portfolio` (팀 `saman-33aa`), 주소 `https://cutnkeep-portfolio.vercel.app`
  - 프로젝트 설정 Root Directory = `Portfolio/site`, Node 22.x, 루트 밖 파일 포함 켬 (`../assets/spreadsheet.json` 때문)
  - 환경변수: `PORTFOLIO_AI_URL`(Render 주소), `PORTFOLIO_DEEP_DB=/tmp/deep_quota.sqlite`
  - `Portfolio/ai` → Render 웹 서비스 `cutnkeep-portfolio-ai`, 주소 `https://cutnkeep-portfolio-ai.onrender.com`
  - Render 빌드 `cd Portfolio/ai && pip install -r requirements.txt gunicorn`, 시작 `gunicorn app:app --workers 1 --threads 4 --timeout 600`
- 이 Vercel 계정은 GitHub 로그인 연결이 없어 Git 자동 배포 대신 CLI 로 올렸다. 저장소 전체 업로드는 파일이 3만 7천 개라 느려서 `site` 와 `assets` 만 임시 폴더에 복사해 올렸다

### 3.4 의도적으로 하지 않은 것

- Ollama 서버 연결 (Render 에는 `gemma4:12b` 를 올릴 수 없어 `OLLAMA_BASE_URL` 은 비어 있음)
- 깊이 추론 횟수의 영구 저장 (Vercel 은 `/tmp` 만 쓸 수 있어 인스턴스가 바뀌면 횟수가 초기화됨)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] Vercel 배포 완료. `/`, `/frontend`, `/console`, `/backend`, `/ai`, `/project`, `/terms`, `/chat`, `/data/erd`, `/data/spreadsheet`, `/api/deep` 모두 200
- [x] Render 배포 완료. `/health` 는 Ollama 가 없어 503
- 챗 질문(`POST /api/chat`)은 Ollama 연결 전이라 동작하지 않는다

### 4.2 부작용 / 리스크

- 챗은 Ollama 연결 전까지 503
- Render 무료 서버는 한동안 요청이 없으면 잠들어 첫 요청이 느림
- 깊이 추론 횟수는 Vercel 인스턴스별 `/tmp` 라 사이트 전체 하루 10번이 정확히 지켜지지 않을 수 있음
- Render 의 `rag_memory.json` 학습 예시는 재시작하면 사라짐

### 4.3 후속 작업

- Ollama 서버 정하기(Oracle Always Free Ampere A1 또는 PC + Cloudflare Tunnel) 후 Render `OLLAMA_BASE_URL` 설정
- 병합은 전체 작업이 끝난 뒤 사용자 지시로

### 4.4 관련 문서

- `Portfolio/README.md`, `docs/HANDOVER.md`
