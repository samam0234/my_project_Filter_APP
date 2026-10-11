# 컷앤킵 포트폴리오

이 폴더는 컷앤킵(Cut & Keep)을 설명하는 문서와, 그 문서를 읽는 전용 사이트를 둔다.
제품 코드(`frontend/`, `console/`, `backend/`)와 운영 서버는 바꾸지 않는다.

기준일은 2026-10-12 인수인계다. 기능의 정본은 `docs/FEATURES.md`, 운영 상태는 `docs/HANDOVER.md`다.

## 문서

| 파일 | 내용 |
|------|------|
| [markdown/01-overview.md](markdown/01-overview.md) | 사이트 소개, 목차, 프로젝트와 기능 요약 |
| [markdown/02-frontend.md](markdown/02-frontend.md) | 사용자 앱 |
| [markdown/03-console.md](markdown/03-console.md) | 운영 콘솔 |
| [markdown/04-backend.md](markdown/04-backend.md) | FastAPI 서버 |
| [markdown/05-ai.md](markdown/05-ai.md) | 비전 · 문장 해석 · 학습 |
| [markdown/06-project.md](markdown/06-project.md) | 사업·업무 관점의 프로젝트 소개 |
| [markdown/07-terms.md](markdown/07-terms.md) | 이 포트폴리오 사이트의 이용약관 |
| [markdown/08-erd.md](markdown/08-erd.md) | 2026-10-11 ERD와 그 이후 테이블 |
| [markdown/09-spreadsheet.md](markdown/09-spreadsheet.md) | Scribble 스프레드시트 10개 시트 |
| [CutNKeep_Portfolio.docx](CutNKeep_Portfolio.docx) | 위 문서를 한 권으로 묶은 Word 문서 |

원본 스프레드시트와 ERD HTML은 로컬 `Scribble/`에만 있고 Git에는 올라가지 않는다.
같은 내용을 이 폴더로 옮겨 두었다.

| 경로 | 내용 |
|------|------|
| `assets/spreadsheet.json` | 시트 전체 |
| `assets/erd/cutnkeep_erd_2026-10-11.html` | ERD 원본 HTML |
| `assets/erd/cutnkeep_erd_2026-10-11.png` | ERD 그림 |

## 사이트 실행

```bash
cd Portfolio/ai
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python app.py
```

```bash
cd Portfolio/site
npm install
npm run dev
```

화면은 `http://127.0.0.1:5190`, 안내는 `http://127.0.0.1:5055` 이다.
안내 모델 `gemma4:12b`가 없으면 챗만 멈추고 페이지는 열린다.

## 사이트

이 폴더 안에 두 프로그램이 있다.

| 경로 | 역할 |
|------|------|
| `site/` | Next.js. 화면과 이 사이트의 API |
| `ai/` | Flask. 포트폴리오를 설명하는 AI 안내. 제품 백엔드와 별도 |

화면의 챗 기록은 브라우저 `localStorage`만 쓴다. 챗봇용 데이터베이스는 두지 않는다. 학습에 쓸 질문과 답은 `Portfolio/ai/data/rag_memory.json`에 남는다.
안내 모델은 운영에도 쓰는 Ollama `gemma4:12b`다.

## 제품과 이 사이트의 차이

컷앤킵 서비스는 React(Vite) 사용자 앱, React 운영 콘솔, FastAPI 백엔드다.
이 포트폴리오 사이트는 그 제품을 설명하는 별도 프로그램이다.
설명 사이트의 화면과 라우트는 Next.js가 맡고, 더 긴 설명은 Flask 안내가 맡는다.
