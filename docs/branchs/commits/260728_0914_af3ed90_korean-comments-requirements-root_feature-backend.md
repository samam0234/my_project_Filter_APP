# feat(repo): 한글 주석 보강 및 requirements 루트 이전 / `af3ed90`

> 브랜치: `feature/backend`  
> 작성일: `2026-07-28 09:14`  
> 작성자: Grok agent  
> 파일명: `260728_0914_af3ed90_korean-comments-requirements-root_feature-backend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(repo): 한글 주석 보강 및 requirements 루트 이전` |
| **커밋 번호 (SHA)** | `af3ed908eec90af091a3cbd574eabead5d1c4a52` |
| **짧은 SHA** | `af3ed90` |
| **브랜치** | `feature/backend` |
| **부모 커밋** | `2be8e7d` |

## 2. 주 커밋 내용

- 백엔드·프론트·콘솔·scripts·tests·training 코드에 **한국어 설명 주석** 추가 (로직 변경 없음)
- `requirements.txt` / `requirements.docker.txt` 를 **저장소 루트**로 이동
- Docker backend 빌드 context 를 루트로 변경, `.dockerignore` 추가
- 커밋 메시지 규칙: **제목 요약 한국어** 로 스킬·가이드 일괄 갱신

## 3. 상세 내용

### 3.1 배경 / 목적

- 코드 가독성: py/ts 파일 역할·흐름을 한글로 설명
- 서버 기준 의존성 배치: Python 서버가 주축이므로 requirements 를 루트에 둠
- 커밋 규칙 변경: 제목 요약 영어 금지, `feat(tts): 음성 인식 추가` 형태 권장

### 3.2 주요 변경 경로

- `backend/app/**`, `frontend/src/**`, `console/src/**`, `scripts/**`, `tests/**`, `training/**`
- `requirements.txt`, `requirements.docker.txt` (루트), `backend/Dockerfile`, `docker-compose.yml`
- `docs/guidance/commit-message.md`, `AGENTS.md`, `.agents/skills/cutnkeep/SKILL.md` 등

### 3.3 커밋 규칙 (신규)

| | 예시 |
|--|------|
| ✅ | `feat(tts): 음성 인식 추가` |
| ❌ | `feat(llm): add to engine` |

## 4. 커밋 관련 결과

- `feature/backend` 에 122 files 반영
- origin 푸시 예정
