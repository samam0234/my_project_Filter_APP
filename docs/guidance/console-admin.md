# Ops Console 가이드

## 위치

- 코드: 저장소 루트 `console/`
- 기술: React + TypeScript + Vite + Tailwind + Zustand
- 포트: **5174**

## 실행

```bash
cd console
npm install
npm run dev
```

Backend(`8000`)가 떠 있어야 Job/헬스 데이터가 채워진다.
콘솔은 **백엔드와 같은 PC** 에서 실행한다 — 전체 작업 조회 API(`/api/v1/console/*`)가 loopback 요청만 허용하기 때문이다.

## 화면

| 메뉴 | 역할 |
|------|------|
| 대시보드 | API/DB 상태, Job 집계, 최근 5건 |
| Job 목록 | 전체 Job 테이블 (회원 작업 + 로그인 기능 이전의 소유자 없는 작업), after 미리보기 링크 |
| **학습 데이터** | 학습 DB `learning_samples` 검수 — 승인 · 정답 고쳐서 승인 · 거절 · 되돌리기 · 삭제 · 선택 일괄 승인/거절 |
| 시스템 | version, dialect, 포트 메모 |
| 바로가기 | frontend / swagger / health |

## 학습 데이터 검수

**승인(approved)한 문장만** 프롬프트 RAG 예시와 LoRA 학습에 쓰인다. 사용자 교정이 틀렸을 때
모든 사용자의 비슷한 요청이 잘못 해석되는 것을 막는 관문이다.

| 출처 | 들어오는 경로 | 검수 포인트 |
|------|---------------|-------------|
| 사용자 교정 `correction` | 결과 화면 "정답 알려주기" (dislike + 정답 JSON) | 정답이 문장과 맞는지 |
| 좋아요 `like` | 결과 화면 👍 — 시스템 해석을 사용자가 확인 | 대부분 그대로 승인 |
| 회원 요청 `request` | 로그인 회원의 업로드 문장 + 시스템 해석 (`LEARNING_COLLECT_REQUESTS`) | 해석이 틀렸으면 **정답 고쳐서 승인** — 실제 사용 문장이 학습 데이터가 되는 주 경로 |
| 처리 실패 `pipeline_failure` | 세그 실패 원본 이미지 (종류 = 세그 실패 이미지) | YOLO 재학습 후보 |
| 의사 라벨 `pseudo_label` | `scripts/pseudo_labeling.py` | 양이 많아 필요할 때만 |

- 같은 문장의 회원 요청은 후보 1건만 만든다 (검수 부담 감소)
- **승인** 시 id 해시로 train / val 이 고정 배정된다 (10% val) — 재학습해도 같은 데이터는 같은 쪽
- **정답 고쳐서 승인**: ParsedPrompt JSON 을 직접 수정. 형식이 틀리면 400
- **삭제**: 원본 사이드카 파일(`data/feedback/*.json|jpg`, 의사 라벨 json)까지 지우고 되돌릴 수 없다.
  행은 내용을 비운 `deleted` 표식으로 남아 기동 시 동기화가 되살리지 않는다
- 승인 · 삭제는 `PROMPT_RAG_REFRESH_SECONDS`(30 s) 안에 RAG 색인에 반영된다
- 승인된 문장으로 LoRA 를 다시 학습하는 방법: [`training/lora/README.md`](../../training/lora/README.md)
  (`augment_prompts.py` → `train_lora.py` → `eval_parser.py`)

## 자동 갱신

30초 간격 + 수동 새로고침 버튼.

## API

| 콘솔 호출 | 백엔드 |
|-----------|--------|
| 헬스 | `GET /health` |
| Job 목록 · 단건 | `GET /api/v1/console/jobs` · `/console/jobs/{id}` |
| after 링크 | `GET /api/v1/console/files/{id}/after` |
| 학습 데이터 목록 · 통계 | `GET /api/v1/console/learning/samples` · `/console/learning/stats` |
| 승인 · 거절 · 되돌리기 | `POST /api/v1/console/learning/samples/{id}/review` |
| 일괄 승인 · 거절 | `POST /api/v1/console/learning/samples/bulk` |
| 삭제 | `DELETE /api/v1/console/learning/samples/{id}` |
| 원본 이미지 | `GET /api/v1/console/learning/samples/{id}/image` |

사용자 앱의 `/api/v1/jobs` 는 로그인 사용자 **본인 작업만** 돌려주므로 콘솔은 쓰지 않는다.

## 보안 주의

콘솔 자체는 **로그인이 없다**. 대신 콘솔 API 는 서버 PC(loopback) 요청만 받는다.
원격에서 써야 하면 reverse proxy 인증·VPN 등 앞단 접근 제어를 한 뒤 `CONSOLE_ALLOW_REMOTE=true`.
