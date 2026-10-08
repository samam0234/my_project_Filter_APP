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
서버 PC 에서 띄우면 로그인 없이 들어가고, 다른 곳(배포)에서는 **관리자 로그인** 화면이 먼저 나온다.

## 관리자 로그인

1. 사용자 앱(:5173)에서 관리자용 계정을 가입한다
2. 서버 `.env` 에 `CONSOLE_ADMINS=그아이디` (여럿이면 쉼표) → 백엔드 재시작
3. 콘솔에서 그 아이디·비밀번호로 로그인 — 헤더에 `관리자 {아이디}` 와 로그아웃 버튼

| 접근 | 결과 |
|------|------|
| 관리자 아이디로 로그인 | 어디서든 사용 |
| 서버 PC, `CONSOLE_REQUIRE_LOGIN=false` (기본) | 로그인 없이 사용 (헤더 `서버 PC (로그인 없음)`) |
| 관리자가 아닌 회원 로그인 | "관리자 계정이 아닙니다" — 콘솔이 세션을 바로 끊는다 |
| 로그인 안 함(원격) | 로그인 화면 |

- **배포:** `CONSOLE_REQUIRE_LOGIN=true`. 같은 서버의 nginx 등 리버스 프록시를 거치면 모든 요청이 127.0.0.1 로 보여
  로그인 없이 열릴 수 있다 (APP_ENV=production 기동 시 preflight 경고)
- 세션이 만료되거나 관리자에서 빠지면 다음 요청(401·403)에서 로그인 화면으로 돌아간다
- 검수 기록 `reviewed_by` 에 `admin:{아이디}` 가 남아 누가 승인·거절했는지 알 수 있다 (서버 PC 는 `console:local`)
- 콘솔과 API 를 다른 도메인에 두면 세션 쿠키가 교차 사이트로 가야 한다 — 같은 도메인(경로 분리) 배치를 권장
- 로컬 개발에서는 사용자 앱(:5173)과 콘솔(:5174)이 같은 쿠키를 쓴다 (쿠키는 포트를 구분하지 않음) — 콘솔에 관리자로 로그인하면
  같은 브라우저의 사용자 앱도 그 계정이 된다. 다른 계정으로 시험할 때는 시크릿 창을 쓴다

## 화면

| 메뉴 | 역할 |
|------|------|
| 대시보드 | API/DB 상태, Job 집계, 최근 5건 |
| Job 목록 | 전체 Job 테이블 (회원 작업 + 로그인 기능 이전의 소유자 없는 작업), after 미리보기 링크 |
| 배치 현황 | 전체 회원의 배치 목록·진행·실패 수 (`GET /api/v1/console/batches`). 진행 중이면 5초마다 갱신. 회원 사진 보호를 위해 이미지는 보여 주지 않음 |
| **회원 관리** | 아이디·이메일 검색, 작업·배치 수, 로그인·잠김 상태. 잠금 해제 · 모든 기기 로그아웃 · 계정 삭제 (아래) |
| **학습 데이터** | 학습 DB `learning_samples` 검수 — 승인 · 정답 고쳐서 승인 · 거절 · 되돌리기 · 삭제 · 선택 일괄 승인/거절 |
| 시스템 | 배포 설정 점검(preflight) · 세그/오픈보캐브/LLM·RAG/배치 큐(Redis)/영상/콘솔 설정 · 저장 공간(작업·배치·영상) · **보관 기간 지난 파일 정리** |
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
- 같은 작업에 좋아요·교정이 오면 새 행 대신 요청 후보를 갱신한다 (출처 승격, 교정이면 정답도 · 승인된 후보는 다시 검수 대기)
- 기본 출처 필터는 **사용자 데이터 (교정·좋아요·요청)** — 의사 라벨 수천 건은 출처 필터에서 따로 선택
- **승인** 시 id 해시로 train / val 이 고정 배정된다 (10% val) — 재학습해도 같은 데이터는 같은 쪽
- **정답 고쳐서 승인**: ParsedPrompt JSON 을 직접 수정. 형식이 틀리면 400
- **삭제**: 원본 사이드카 파일(`data/feedback/*.json|jpg`, 의사 라벨 json)까지 지우고 되돌릴 수 없다.
  행은 내용을 비운 `deleted` 표식으로 남아 기동 시 동기화가 되살리지 않는다
- 승인 · 삭제는 `PROMPT_RAG_REFRESH_SECONDS`(30 s) 안에 RAG 색인에 반영된다
- 승인된 문장으로 LoRA 를 다시 학습하는 방법: [`training/lora/README.md`](../../training/lora/README.md)
  (`augment_prompts.py` → `train_lora.py` → `eval_parser.py`) — 한 번에: `python scripts/retrain_lora.py`
- 승인 카드의 `재학습 N/200` = 승인된 사용자 문장 수 / 재학습 기준 (`LORA_RETRAIN_MIN_NEW`)

## 회원 관리

| 동작 | 결과 |
|------|------|
| 잠금 해제 | 로그인 실패(`LOGIN_MAX_FAILURES`)로 잠긴 계정을 바로 풀어 줌 |
| 로그아웃 | 그 회원의 모든 로그인 세션 삭제 — 다음 요청부터 비로그인 (비밀번호 유출 의심 시) |
| 삭제 | **되돌릴 수 없음.** 아이디를 다시 입력해야 실행. 계정 · 세션 · 작업 · 배치 · 영상 보관본과 결과 파일 삭제. 학습 데이터(검수 문장)는 남기고 계정 연결(`user_id`)만 끊음 — 지울 문장은 "학습 데이터" 화면에서 |

- 관리자(`CONSOLE_ADMINS`) 계정과 지금 로그인한 본인은 삭제할 수 없다 (콘솔에 아무도 못 들어가는 상황 방지)
- 삭제는 서버 로그에 `회원 삭제 ... by=관리자아이디` 로 남는다
- 비밀번호는 해시로만 저장돼 콘솔에서도 볼 수 없다 — 회원에게 사용자 앱의 "비밀번호 재설정"을 안내

## 시스템 · 저장 공간 정리

- **배포 설정 점검**: `python -m app.core.preflight` 와 같은 결과. production 에서 `error` 가 있으면 백엔드가 뜨지 않는다
- **런타임**: 화면을 연다고 모델을 로드하지 않는다 — 첫 요청 전이면 세그 런타임이 "로드 전"
- **대상 마스크 처리 · 해석 체인**: 겹침 규칙(`MASK_EXCLUSIVE`), GrabCut·CLAHE 켬/끔, 어려운 사례 수집 기준, LangChain 다수결 여부 — 지정하지 않은 물체가 섞이는 문제의 설정값을 한눈에
- **배치 큐**: `BATCH_USE_CELERY=true` 일 때만 Redis 를 1초 ping. 연결 안 됨이면 배치는 API 프로세스에서 처리된다
- **저장 공간**: 단일 작업 · 배치 · 영상 별 용량, `FILE_RETENTION_HOURS` 가 지난 파일 수, 디스크 남은 공간(10% 미만이면 빨강)
- **정리**: "정리 미리 보기"로 지울 파일 수·용량을 먼저 보고 "지금 정리". `scripts/cleanup.py` 와 같은 함수
  (`app/services/retention.py`). 작업 기록(DB 행)은 남는다. 정리 실행은 서버 로그에 관리자 이름과 함께 남는다
- 정기 실행: `python scripts/cleanup.py` (`--dry-run` 으로 집계만) — 서버 cron/작업 스케줄러에 등록

## 자동 갱신

30초 간격 + 수동 새로고침 버튼.

## API

| 콘솔 호출 | 백엔드 |
|-----------|--------|
| 접근 확인 · 로그인 · 로그아웃 | `GET /api/v1/console/me` · `POST /api/v1/auth/login` · `/auth/logout` |
| 회원 목록 · 잠금 해제 · 세션 끊기 · 삭제 | `GET /api/v1/console/users` · `POST /users/{id}/unlock` · `POST /users/{id}/sessions/revoke` · `DELETE /users/{id}` |
| 시스템 스냅샷 · 정리 | `GET /api/v1/console/system` · `POST /api/v1/console/system/cleanup?dry_run=` |
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

원격 접근은 관리자 로그인(`CONSOLE_ADMINS`)으로 한다. `CONSOLE_ALLOW_REMOTE=true` 는 로그인 없이 누구에게나 여는 예전 방식이라
앞단(VPN·리버스 프록시 인증)으로 막은 경우가 아니면 쓰지 않는다.
