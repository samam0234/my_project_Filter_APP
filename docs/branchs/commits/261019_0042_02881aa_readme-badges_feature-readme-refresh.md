# 루트 · 포트폴리오 README 에 기술 배지와 프레임워크 절 추가 / `02881aafa6080b1e8a2eea8e69b6222cf0f8ecc1`

> 브랜치: `feature/readme-refresh`  
> 작성일: `2026-10-19 00:42`  
> 작성자: `agent`  
> 파일명: `261019_0042_02881aa_readme-badges_feature-readme-refresh.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(readme): 루트 · 포트폴리오 README 에 기술 배지와 프레임워크 절 추가` |
| **커밋 번호 (SHA)** | `02881aafa6080b1e8a2eea8e69b6222cf0f8ecc1` |
| **짧은 SHA** | `02881aa` |
| **브랜치** | `feature/readme-refresh` |
| **부모 커밋** | `acf2bf833d36b5bd5f811edae75b600799379f84` |

## 2. 주 커밋 내용

- `README.md` 머리에 한 줄 소개와 기술 배지(FastAPI · React · Vite · LangGraph · Ollama · Docker · Cloudflare)를 추가
- `README.md` 에 "5. 프레임워크" 절을 추가하고 목차에 등록 (화면 · API · 해석 · 저장소 · 배포)
- `Portfolio/README.md` 머리에 소개와 배지를 추가하고 "2. 프레임워크" 절을 넣어 뒤 절 번호를 한 칸씩 밀음

## 3. 상세 내용

### 3.1 배경 / 목적

1~2차 커밋 뒤에 작업 트리에 README 두 개의 수정이 더 생겨 있었다 (내가 하지 않은 수정). 병합 전에 같은 브랜치에 커밋해 함께 병합한다.

### 3.2 변경 범위

- 수정된 경로: `README.md`, `Portfolio/README.md` (177줄 추가 · 15줄 삭제)

### 3.3 기술 포인트

- 배지의 버전은 `Portfolio/site/package.json`(Next.js 15.5.27 · React 19.1.1) · `Portfolio/ai/requirements.txt`(Flask 3.1.2 · LangGraph 0.6.6 · LangChain 0.3.27 · Chroma 1.5.9) · 제품 스택(FastAPI 0.143 · React 18 · Vite 7)과 맞는다
- 배지 이미지는 외부(img.shields.io)에서 불러온다. 오프라인이면 대체 텍스트로 보인다

### 3.4 의도적으로 하지 않은 것

- 내용 재작성 — 받은 수정을 그대로 커밋만 했다

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] `pytest tests/structure` — 13개 중 12개 통과, 남은 1개는 `.env.example` 의 `PROMPT_CHROMA_*` 누락 (기존 실패)
- [ ] 배지 이미지 렌더링 — GitHub 에서 확인하지 못함

### 4.2 부작용 / 리스크

- 외부 배지 서비스에 의존한다
- `Portfolio/README.md` 의 절 번호가 바뀌어, 다른 문서가 그 절 번호로 링크하면 어긋난다 (`#6-공개-배포-2026-10-12-기준` 은 `#7-…` 로 바뀜) — 같은 브랜치의 후속 커밋에서 두 README 의 링크를 고쳤다

### 4.3 후속 작업

- (처리됨) `Portfolio/ai/README.md` · `Portfolio/site/README.md` 의 링크를 7절로 수정

### 4.4 관련 문서

- `docs/branchs/commits/261018_2306_5a94dd7_readme-product-docs_feature-readme-refresh.md`
