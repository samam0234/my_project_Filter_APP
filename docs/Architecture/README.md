# Architecture — 시스템 구조

> 컷앤킵이 어떤 조각으로 나뉘고, 요청과 데이터가 그 사이를 어떻게 흐르는지 정리하는 폴더.

전체 그림을 빠르게 보려면 루트 [README의 3 · 4절](../../README.md#3-어떻게-동작하나)(처리 흐름 · 시스템 구성 mermaid)을 먼저 보고, 계층과 흐름을 자세히 볼 때 이 폴더로 온다.

## 한눈에

```text
사용자 ─▶ Cloudflare Worker / Caddy(HTTPS) ─▶ nginx(frontend) ─▶ FastAPI backend
                                                                   ├─ Router → Schema → Service/Workflow → Repository → Model → DB
                                                                   ├─ LangGraph: 해석 → 전처리 → 세그 → 검증(재시도) → 효과 → 피드백
                                                                   ├─ MariaDB (서비스 DB · 학습 DB) · Redis
                                                                   └─ Ollama (운영자 PC, SSH 터널)
운영자 ─▶ console(:5174, 관리자 PC) ─▶ /api/v1/console/*
```

## 문서 목록

| 파일 | 내용 | 이럴 때 |
|------|------|---------|
| [overview.md](./overview.md) | 전체 아키텍처 한눈에 보기 | 처음 구조를 볼 때 |
| [apps.md](./apps.md) | frontend / console / backend 역할 분리 | 기능을 어느 앱에 넣을지 정할 때 |
| [layers.md](./layers.md) | Router · Schema · Service · Repository · DB 계층 | 백엔드 코드를 어디에 쓸지 정할 때 |
| [data-flow.md](./data-flow.md) | 요청 → 응답 · 피드백 데이터 흐름 | 업로드 한 건이 어디를 거치는지 볼 때 |
| [docker-topology.md](./docker-topology.md) | `cut_and_keep` Compose 토폴로지 | 컨테이너 · 네트워크 · 포트를 볼 때 |

## 지켜지는 원칙

| 원칙 | 내용 |
|------|------|
| 계층 고정 | 라우터는 SQL을 직접 쓰지 않는다 · 레포지토리는 OpenCV와 LLM을 모른다 · ORM 모델과 API 스키마를 섞지 않는다 |
| 앱 분리 | 사용자 앱은 본인 데이터만(`/api/v1/*`), 콘솔은 전체(`/api/v1/console/*`). 콘솔은 공개하지 않는다 |
| DB 분리 | 서비스 DB와 학습 DB는 외래 키 없이 값으로만 연결. 학습 DB가 꺼져도 서비스는 계속 |
| 파일은 경로만 | 이미지 · 영상은 DB에 넣지 않고 경로만 기록 |
| 작은 공개면 | 공개 포트는 22 · 80 · 443. DB · Redis · Adminer는 루프백 |
| 해석은 로컬 | 사진을 외부 모델에 보내지 않는다. 문장 해석은 운영자 PC의 Ollama |

## 관련 계획 문서

- [`../plan/LOGIC_STRUCTURE.md`](../plan/LOGIC_STRUCTURE.md) — 통합 로직 구조
- [`../plan/PROJECT_STRUCTURE.md`](../plan/PROJECT_STRUCTURE.md) — 폴더 · 모듈 구조
- [`../plan/DATABASE.md`](../plan/DATABASE.md) — DB 설계
- [`../plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md) — 지금 스냅샷
- [`../WORKFLOW.md`](../WORKFLOW.md) — LangGraph 흐름

## 작성 규칙

- 구현이 바뀌면 이 폴더를 먼저 갱신한다. 특히 계층 규칙 · 앱 경계 · 포트가 바뀔 때.
- 다이어그램은 ASCII 또는 mermaid를 쓴다.
- 지금 운영 구성의 정본은 [`../HANDOVER.md`](../HANDOVER.md)다. 이 폴더와 다르면 HANDOVER를 따르고 이 폴더를 고친다.
