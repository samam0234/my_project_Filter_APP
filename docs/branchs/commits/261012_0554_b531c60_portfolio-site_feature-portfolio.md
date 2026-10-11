# 설명 사이트와 안내 챗 / `b531c60a5726af4061f392fbb7afa3a74b544b0e`

> 브랜치: `feature/portfolio`  
> 작성일: `2026-10-12 05:54`  
> 작성자: `agent`  
> 파일명: `261012_0554_b531c60_portfolio-site_feature-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(portfolio): 설명 사이트와 안내 챗 추가` |
| **커밋 번호 (SHA)** | `b531c60a5726af4061f392fbb7afa3a74b544b0e` |
| **짧은 SHA** | `b531c60` |
| **브랜치** | `feature/portfolio` |
| **부모 커밋** | `9c4679734400520ff2b35cc1e28f90d2408e6e66` |

## 2. 주 커밋 내용

- `Portfolio/site`에 Next.js 설명 사이트를 추가함. 포트 5190
- 소개, 사용자 앱, 운영 콘솔, 백엔드, AI, ERD, 스프레드시트, 안내 챗, 프로젝트 소개, 이용약관
- 푸터는 프로젝트 소개를 이용약관 왼쪽에 둠
- `Portfolio/ai`에 Flask 안내를 추가함. 포트 5055. 제품 FastAPI와 별도
- LangGraph가 분류·검색·답변을 나누고, 글자 2-gram과 BM25로 문서를 찾고, LangChain이 Ollama `gemma4:12b`를 호출함
- 대화는 브라우저 `localStorage`(`cnk-portfolio-chat-v1`)만 씀. 챗봇 데이터베이스 없음
- 백엔드 문서의 “사진은” 오타를 고치고 Word를 다시 만듦

## 3. 상세 내용

### 3.1 배경 / 목적

문서 커밋 다음에, 같은 설명을 브라우저에서 읽고 더 묻고 싶을 때 안내 챗으로 잇기 위함.
화면과 이 사이트의 API는 Next.js가 맡고, 모델 호출은 Flask가 맡는다.

### 3.2 변경 범위

- 추가: `Portfolio/site/**`, `Portfolio/ai/**`, `Portfolio/.gitignore`
- 수정: `Portfolio/README.md`, `Portfolio/markdown/04-backend.md`, `Portfolio/CutNKeep_Portfolio.docx`
- 제품 `frontend/`, `console/`, `backend/`, `.env`는 수정하지 않음

### 3.3 기술 포인트

- Next.js 15.5.27, React 19. 사이트 전용이며 제품 앱의 React 18과는 다름
- ERD는 Scribble HTML을 iframe으로 그대로 보여 줌. `signup_pending`은 그림 밖에 표로 적음
- 시트는 `Portfolio/assets/spreadsheet.json`을 탭으로 보여 줌
- `gemma4`는 생각 토큰을 먼저 쓰므로 안내에서는 `reasoning=False`. 제품 기본 모델 `gemma4:e4b`는 바꾸지 않음
- 12b가 없으면 챗만 503이고 나머지 페이지는 열림

### 3.4 의도적으로 하지 않은 것

- develop/main 병합, push, 배포
- `gemma4:12b` 자동 다운로드
- 챗 기록을 서비스 DB나 학습 DB에 저장
- 제품 화면의 회원 목록 스크린샷

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `npm run build` 통과 (Next.js 15.5.27, 정적 페이지 14)
- [x] Word 스키마 검증 통과. 본문에 “사진은 약 20MB”가 있음
- [x] Edge로 홈, 모바일 프론트, 시트 탭, ERD iframe, 안내 챗을 확인
- [x] 안내 챗은 문서에 있는 문장으로 답하고, 새로고침 뒤 localStorage에 남고, 지우면 `[]`
- [x] 빈 messages는 400, Flask가 꺼지면 프록시가 503
- [ ] Docker 확인 — 해당 없음
- 결과 서술: 로컬 `http://127.0.0.1:5190`, 안내 `http://127.0.0.1:5055`

### 4.2 부작용 / 리스크

12b는 첫 호출이 수십 초 걸린다. 모델이 없으면 챗만 멈춘다.
시트 숫자는 2026-10-11 기준이라 배포 상태와 테스트 수는 인수인계가 우선이다.
Next 15.5.27에 남은 권고는 postcss와 sharp 전달 의존성이고, 고치려면 Next 16이다.

### 4.3 후속 작업

`feature/portfolio`를 develop에 병합하는 일은 사용자가 시킬 때만 한다.

### 4.4 관련 문서

- `Portfolio/README.md`
- `docs/HANDOVER.md`
- `docs/FEATURES.md`
