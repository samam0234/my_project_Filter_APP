# console — Cut & Keep 운영 콘솔

> 서비스를 **쓰는** 화면이 아니라 서비스를 **보는** 화면. 전체 작업 · 배치 · 학습 데이터 검수 · 회원 · 시스템을 관리자만 다룬다.

운영자용 React 앱이다. 사용자 앱([`frontend/`](../frontend/README.md))과 저장소 폴더 · 포트 · 배포 단위가 다르다.
화면 규칙과 빌드 방식을 다시 배우지 않도록 기술은 사용자 앱과 같은 계열로 맞췄다.

| 항목 | 내용 |
|------|------|
| 로컬 주소 | http://localhost:5174 (Vite가 `/api` · `/health`를 `localhost:8000`으로 넘김) |
| 기술 | React 18 · TypeScript · Vite 7 · Tailwind CSS · Zustand · axios |
| 테스트 | Vitest **21개** (2026-10-12) — 학습 화면 중심 |
| 배포 | **공개 서버에 올리지 않는다.** Docker Compose에도 콘솔 서비스가 없다. 관리자 PC에서 띄워 서버의 `/api/v1/console/*`를 호출한다 |

---

## 1. 왜 따로 만들었나

컷앤킵의 학습 순환에는 관문이 하나 필요하다.

사용자가 틀린 정답을 알려 주면, 그 문장과 비슷한 **다른 사람의 요청까지 잘못 해석될 수 있다.** 그래서 정답 알려주기 · 좋아요 · 회원 요청은 곧바로 학습에 들어가지 않고, 이 콘솔에서 운영자가 승인한 것만 RAG 예시와 LoRA 학습 데이터가 된다.

그 밖에 사용자 앱으로는 할 수 없는 일 — 소유자와 관계없는 전체 조회, 회원 잠금과 삭제, 디스크와 설정 점검 — 을 이 앱이 맡는다. 사용자 앱의 `GET /api/v1/jobs`는 본인 작업만 돌려주므로 콘솔은 그 API를 쓰지 않고 `/console/*`를 쓴다.

| | `frontend/` | `console/` |
|--|-------------|------------|
| 대상 | 일반 사용자 · 회원 | 운영자 (`CONSOLE_ADMINS`) |
| 포트 | 5173 | 5174 |
| 핵심 | 올리기 · 문장 · 결과 | 검수 · 모니터링 · 관리 |
| 공개 | Cloudflare Worker · 서버 nginx | 공개하지 않음 |
| API | `/api/v1/*` (본인 것만) | `/api/v1/console/*` (전체) |

---

## 2. 메뉴

| 메뉴 | API | 내용 |
|------|-----|------|
| 로그인 | `GET /api/v1/console/me` | 관리자 확인. 원격에서는 이 화면이 먼저 |
| 대시보드 | `/health` · `/console/jobs` | 상태 · 집계 · 최근 작업 |
| 작업 목록 | `/console/jobs` · `/console/files/{id}/*` | 사진 · 영상 · GIF. 소유자와 관계없이 전체 |
| 배치 현황 | `GET /console/batches` | 진행률과 실패 수. **회원 사진은 보여 주지 않는다** (5초마다 갱신) |
| 학습 데이터 | `/console/learning/*` | 승인 · 정답 고쳐서 승인 · 거절 · 일괄 처리 · 삭제 |
| 회원 관리 | `/console/users*` | 검색 · 잠금 해제 · 세션 끊기 · 계정 삭제 |
| 시스템 | `/console/system` · `POST .../cleanup` | 배포 설정 점검 · 세그 런타임 · 해석 체인 · 지우기 엔진(LaMa · Telea) · 배치 큐 · 저장 공간 · 정리 미리 보기 / 실행 |
| 바로가기 | — | 사용자 앱 · Swagger · health |

화면 전체는 30초마다, 또는 수동 새로고침으로 갱신한다.

### 학습 데이터 검수

| 출처 | 들어오는 곳 | 검수 |
|------|-------------|------|
| `correction` | 결과 화면의 정답 알려주기 | 문장과 정답이 맞는지 |
| `like` | 좋아요 | 대체로 그대로 승인 |
| `request` | 회원 업로드 문장과 그때의 해석 | 틀리면 정답을 고쳐 승인 |
| `pipeline_failure` | 세그 실패 사진 | YOLO 재학습 후보 |
| `pseudo_label` | 의사 라벨 스크립트 | 필요할 때만 |

- 같은 문장의 회원 요청은 후보를 한 건만 만든다.
- 승인하면 id 해시로 **train / val이 고정**된다 (val 약 10%). 다시 학습해도 같은 표본은 같은 쪽에 남는다.
- 승인이나 삭제는 약 **30초 안에** RAG 색인에 반영된다.
- 삭제하면 사이드카 파일까지 지우고, 행은 비운 `deleted`로 남겨 다음 기동 때 되살아나지 않게 한다.
- 검수자 이름은 `admin:{아이디}`로 남는다. 서버 PC에서 로그인 없이 본 경우는 `console:local`이다.
- 화면의 `재학습 N/200`은 LoRA 재학습 기준(`LORA_RETRAIN_MIN_NEW`)까지의 숫자다. 재학습 버튼은 아직 없고, 기준에 닿으면 `scripts/retrain_lora.py`를 돌린다.

### 회원 관리

- 회원 삭제는 되돌리지 못한다. **아이디를 다시 입력해야** 실행된다.
- 계정 · 세션 · 작업 · 배치 · 결과 파일 · 실패 사진을 지운다. 학습 문장은 남기고 회원 연결만 끊는다.
- 비밀번호는 해시만 있어 콘솔에서도 볼 수 없다.
- 관리자 계정은 사용자 앱에서 스스로 탈퇴할 수 없다. 콘솔에 들어갈 사람이 사라지는 상황을 막기 위해서다.

### 시스템

- 시스템 화면은 모델을 미리 올리지 않는다. 첫 요청 전이면 세그 런타임이 "로드 전"이다.
- 배치 큐는 `BATCH_USE_CELERY=true`일 때만 Redis를 확인한다. 아니면 API 프로세스가 배치를 처리한다.
- 보관 기간이 지난 파일을 미리 보고 즉시 정리할 수 있다 (백엔드도 매시간 자동으로 같은 정리를 한다).

---

## 3. 접근 규칙

| 조건 | 결과 |
|------|------|
| `CONSOLE_ADMINS`에 있는 아이디로 로그인 | 어디서든 사용 |
| 서버 PC이고 `CONSOLE_REQUIRE_LOGIN=false` | 로그인 없이 사용. 머리글에 서버 PC라고 표시 |
| 관리자가 아닌 회원 | 세션을 바로 끊고 거절 |
| 로그인 없이 원격 | 로그인 화면 |

- 운영 서버는 `CONSOLE_REQUIRE_LOGIN=true`다.
- 관리자 아이디는 **가입을 먼저 하고** 나중에 `.env`에 적는다. 없는 아이디를 미리 적어 두면, 그 아이디를 먼저 가입한 사람이 관리자가 된다.
- `CONSOLE_ALLOW_REMOTE=true`는 로그인 없이 여는 예전 방법이다. 앞단 인증이 없으면 쓰지 않는다.
- 리버스 프록시 뒤에서 모든 요청이 127.0.0.1로 보이면, 로그인 설정이 느슨할 때 콘솔이 열릴 수 있다. 운영 기동 점검(preflight)이 이 경우를 경고한다.
- 로컬에서는 5173과 5174가 쿠키를 공유한다. 콘솔에 관리자로 로그인하면 같은 브라우저의 사용자 앱도 그 계정이 된다. 다른 계정 시험은 시크릿 창으로.

자세히: [`docs/guidance/console-admin.md`](../docs/guidance/console-admin.md)

---

## 4. 구조

```text
console/
├── src/
│   ├── main.tsx · App.tsx      진입점 · 메뉴 라우팅 · 30초 갱신 · 관리자 확인
│   ├── api/client.ts           axios → /api/v1/console/*
│   ├── pages/                  Dashboard · Jobs · Batches · Learning · Users · System · Links · Login
│   ├── components/             Sidebar · StatCard
│   ├── hooks/useConsoleData.ts 데이터 불러오기
│   ├── store/useConsoleStore.ts
│   └── types/
├── vite.config.ts              dev 5174 · 프록시
└── package.json
```

---

## 5. 실행

**최초 1회 `npm install`이 필요하다.** `node_modules` 없이 `npm run dev`를 하면 `vite`를 찾지 못해 실패한다.

```bash
cd console
npm install
npm run dev          # http://localhost:5174
```

- 표의 데이터는 백엔드(:8000)가 떠 있어야 채워진다. 화면 자체는 백엔드 없이도 뜬다.
- 백엔드 `CORS_ORIGINS`에 5174가 들어 있어야 한다 (`.env.example` 기본값에 포함).
- 운영 서버에 붙이려면 관리자 PC에서 콘솔을 띄우고 서버 API로 연결한다. 콘솔 화면은 서버에 올리지 않는다.

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 |
| `npm run build` | 타입 검사 + 빌드 |
| `npm run test` | Vitest (21개) |
| `npm run lint` | ESLint |

---

## 6. 알려진 한계와 방향

- 콘솔을 공개 주소에 올리지 않았다. 올리려면 Cloudflare Access 같은 접근 제한이 먼저다.
- 2026-10-08 디자인 정리는 사용자 앱만 했다. 콘솔은 운영용 다크 화면을 유지한다.
- 재학습 버튼은 아직 없다.

콘솔은 관리자 수가 아주 적은 도구로 둔다. 사용자 앱처럼 누구나 여는 서비스로 만들지 않는다.
검수 기록과 삭제 기록은 서버 로그에 관리자 이름과 함께 남긴다. 학습 품질은 모델 크기보다 이 화면에서 거른 문장에 더 좌우된다.

---

## 관련 문서

- [`docs/guidance/console-admin.md`](../docs/guidance/console-admin.md) — 콘솔 운영 · 학습 데이터 검수
- [`docs/guidance/learning-loop.md`](../docs/guidance/learning-loop.md) — 승인 문장이 RAG · LoRA로 들어가는 경로
- [`Portfolio/markdown/03-console.md`](../Portfolio/markdown/03-console.md) — 콘솔 소개
- [`RUN.md`](../RUN.md)
