# API Documentation

Base URL: `http://localhost:8000` · 대화형 문서: `/docs` (Swagger UI)
프론트(5173)·콘솔(5174) dev 서버는 Vite 프록시로 `/api`, `/health` 를 이 주소로 넘긴다.
백엔드가 꺼져 있으면 프록시가 **본문 없는 500** 을 돌려준다 (화면에는 "서버에 연결할 수 없음" 안내).

## 접근 정책 한눈에

| 기능 | 비로그인 | 로그인 회원 |
|------|----------|-------------|
| 작업실 처리 (배경 제거·블러·크롭·지우기) | ✅ 결과를 응답에 담아 **다운로드만** — 서버에 기록·파일·실패 케이스를 남기지 않음 | ✅ 저장 (작업 기록 · 결과 파일 보관) |
| 작업 기록 · 작업 상세 | 🔒 로그인 안내 | ✅ **본인 작업만** |
| 결과 파일 `/files/*` | 🔒 404 | 본인 작업만 |
| 피드백 · 정답 알려주기 | ✖ (저장된 작업이 없음) | ✅ 본인 작업만 |
| 배치 | 🔒 로그인 안내 | ✅ 본인 배치만 조회 |

- 🔒 = 401 (로그인 필요). 남의 작업·파일·배치는 존재를 알리지 않도록 **404**
- 소유자 없는(로그인 기능 이전) 작업은 사용자 API 로 보이지 않고 **운영 콘솔 API** 로만 조회
- 세션은 HttpOnly 쿠키 — 상세 [`guidance/auth.md`](guidance/auth.md)

---

## Health

`GET /health`

```json
{ "status": "ok", "version": "0.1.0", "phase": 1, "db_dialect": "sqlite" }
```

---

## Auth — 계정

세션은 **HttpOnly · SameSite=Lax 쿠키**(`SESSION_COOKIE_NAME`, 기본 `cnk_session`)로만 주고받는다.
상세 규칙·보안: [`guidance/auth.md`](guidance/auth.md)

| 엔드포인트 | 요청 JSON | 응답 |
|------------|-----------|------|
| `POST /api/v1/auth/signup` | `username`, `email`, `password`, `display_name?` | 201 사용자 + 세션 쿠키 · 400 규칙 위반 · 409 중복 |
| `POST /api/v1/auth/login` | `username`, `password` | 200 사용자 + 쿠키 · 401 불일치 · 429 잠금 |
| `POST /api/v1/auth/logout` | — | 200, 서버 세션 폐기 + 쿠키 삭제 |
| `GET /api/v1/auth/me` | — | 200 사용자 · 401 비로그인 |
| `POST /api/v1/auth/find-id` | `email` | 200 **항상 같은 안내** (아이디는 메일로만) |
| `POST /api/v1/auth/password/request` | `username`, `email` | 200 **항상 같은 안내** (일치하면 6자리 코드 메일) |
| `POST /api/v1/auth/password/reset` | `username`, `code`, `new_password` | 200 성공(모든 세션 로그아웃) · 400 코드 오류/만료/규칙 위반 |

사용자 응답: `{ "id", "username", "email", "display_name", "created_at" }`

---

## Upload — 단일 이미지 처리

`POST /api/v1/upload` · `multipart/form-data`

| 필드 | 설명 |
|------|------|
| `file` | JPEG / PNG / WebP, 최대 20 MB (`MAX_UPLOAD_SIZE_MB`) |
| `prompt` | 자연어 요청 1~1000자 |

파이프라인을 **동기**로 실행한다.

- **속도 제한:** 분당 비로그인 IP 6회 · 회원 20회 (`UPLOAD_RATE_*`). 넘으면 `429` + `Retry-After` 헤더
- **회원 요청은 학습 데이터 후보:** 문장과 시스템 해석이 운영 콘솔 검수 목록에 들어간다 (`LEARNING_COLLECT_REQUESTS`)

- **로그인:** `jobs` 테이블에 저장(`user_id` 연결), 결과 파일 보관, `before_url`/`after_url` 은 파일 경로, `saved: true`
- **비로그인:** 저장하지 않음 — DB 기록·결과 파일·실패 케이스(학습 재료)를 남기지 않는다.
  `after_url` 은 결과 이미지 **data URL**(`data:image/png;base64,…`), `before_url` 은 `null`, `saved: false`
LLM 이 Ollama 일 때 요청당 약 3~5 초 (대부분 LLM). 처리 중에도 다른 API 는 바로 응답한다 (스레드풀 실행).

응답:

```json
{
  "job_id": "8a901e7b…",
  "status": "ok",
  "parsed_prompt": {
    "target": ["person"],
    "effect": "remove_bg",
    "intensity": 15,
    "crop": false,
    "selector": { "position": "front", "rank": null, "count": 1,
                  "attributes": ["red helmet", "neon yellow vest"] }
  },
  "before_url": "/api/v1/files/8a901e7b…/before",
  "after_url": "/api/v1/files/8a901e7b…/after",
  "quality_score": 0.92,
  "message": "ok",
  "feedback_saved": false,
  "saved": true
}
```

| `status` | 의미 |
|----------|------|
| `ok` | 마스크 품질 통과, 효과 적용 |
| `fallback` | 면적·confidence 미달 (1회 재시도 후에도) — best-effort 효과 |
| `failed` | 요청 대상 없음·빈 마스크 등. `message` 에 이유 (예: "요청한 대상(bus)을 이미지에서 찾지 못했습니다. 감지된 대상: car, person"). 결과 이미지는 원본 유지 |

`parsed_prompt` 필드 정의 (정본 `backend/app/services/prompt_spec.py`):

| 필드 | 값 |
|------|-----|
| `target` | COCO 클래스 소문자 목록 |
| `effect` | `remove_bg` · `blur` · `crop` · `none` (대상 **남김**) / `remove_object` (대상 **지움**) |
| `intensity` | 0~100 (블러) |
| `crop` | 추가 크롭 여부 |
| `selector` | `null` = 대상 클래스 전부. 또는 `position`(front·back·left·right·center·largest·smallest) · `rank`(몇 번째) · `count` · `attributes`("색 부위") |

### 결과 파일

| 엔드포인트 | 내용 |
|------------|------|
| `GET /api/v1/files/{job_id}/before` | 원본 JPEG — **작업 소유자만** (그 외 404) |
| `GET /api/v1/files/{job_id}/after` | 결과 — `remove_bg` 는 투명 PNG, 나머지는 JPEG — **작업 소유자만** |

파일은 `backend/data/uploads/{job_id}/` 에 있으며 `FILE_RETENTION_HOURS` 뒤 `scripts/cleanup.py` 가 지운다.

---

## Jobs — 처리 이력

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/v1/jobs?limit=50` | **로그인 사용자 본인** 작업 최근 목록 (상한 200, 최신순) · 비로그인 401 |
| `GET /api/v1/jobs/{job_id}` | 본인 작업 단건 · 없거나 남의 작업이면 404 · 비로그인 401 |

```json
{
  "job_id": "…", "prompt": "왼쪽에서 두 번째 사람 지워줘", "status": "ok",
  "parsed_prompt": { "...": "..." }, "quality_score": 0.76,
  "before_url": "/api/v1/files/…/before", "after_url": "/api/v1/files/…/after",
  "backend": "yolo", "message": "ok", "feedback_saved": false,
  "created_at": "2026-09-30T03:59:10"
}
```

`created_at` 은 UTC (시간대 표기 없음).

---

## Feedback

`POST /api/v1/feedback` · JSON · **로그인 필요, 본인 작업만** (남의 작업 404)

```json
{ "job_id": "…", "vote": "like" | "dislike", "comment": "선택, 최대 2000자" }
```

- DB `feedbacks` + `data/feedback/{case_id}.json` 사이드카 (프롬프트·해석 결과 포함)
- **dislike 의 `comment` 가 ParsedPrompt JSON 이면 LoRA 학습 정답으로 쓰인다**
  (사용자 앱 작업 상세 화면의 "정답 알려주기" 가 이 형식으로 보낸다)

```json
{ "job_id": "…", "vote": "dislike",
  "comment": "{\"target\":[\"person\"],\"effect\":\"remove_bg\",\"selector\":{\"position\":\"front\",\"count\":1,\"attributes\":[\"red helmet\"]}}" }
```

---

## Batch

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/batch` | **로그인 필요** · `multipart`: `files[]`(최대 `MAX_BATCH_SIZE`), `prompt` → 파일 저장 후 `queued`. 기본은 프로세스 안에서 한 장씩 처리. `BATCH_USE_CELERY=true` 이면 Redis 워커. 이미지 시그니처가 아니면 400 (배치를 만들지 않음) |
| `GET /api/v1/batch` | **로그인 필요** · 내 배치 목록 (최신순, `limit` ≤ 100) |
| `GET /api/v1/batch/{job_id}` | **로그인 필요** · 본인 배치 상태·진행률·`prompt`·`item_results[]`(각각 `index`·`filename`·`status`·`backend`·`quality_score`·`message`·`before_url`·`after_url`)·`download_url`. 없거나 남의 배치면 `status: "not_found"` |
| `GET /api/v1/batch/{job_id}/items/{index}/{before\|after}` | **본인만** · 원본 / 결과 이미지. 남의 것·없는 항목·만료는 404 |
| `GET /api/v1/batch/{job_id}/download` | **본인만** · 처리된 결과를 zip 으로 (`{원본이름}_result.png`) |

- 한 장 한 장이 **단일 업로드와 같은 파이프라인**을 탄다 — 인스턴스 선택(위치·순서·색), 마스크 원본 크기 복원, 재시도. 문장은 한 번만 해석(LLM 1회)
- 한 항목이 실패(`status: "failed"`)해도 나머지는 계속 처리. 실패 케이스는 학습 후보로 저장하지 않음
- 결과·원본 파일은 `FILE_RETENTION_HOURS`(기본 24 h) 뒤 `scripts/cleanup.py` 가 지운다 — 이후 이미지 요청은 404 (DB 행은 남음)

→ DB `batch_jobs`. 워커는 `backend/app/tasks/batch_tasks.py`.

## Video

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/video` | `multipart`: `file`(mp4/avi/webm/mov/mkv), `prompt`. 프레임 세그 후 MJPG avi. **비로그인**은 첨부 응답만(저장 없음). **회원**은 `uploads/videos/{job_id}` 보관 |
| `GET /api/v1/video/{job_id}` | **본인만**. 비로그인·남의 영상이면 404 |

검출이 없는 프레임은 직전 마스크를 유지한다. 상한은 `VIDEO_MAX_FRAMES` · `VIDEO_MAX_SECONDS`.
프레임마다 selector(위치·순서·개수·색)로 인스턴스를 고른다 — 프레임 사이 추적은 없어 사람이 겹치거나 지나가면 선택이 바뀔 수 있다.
세그 모델은 프로세스 공용(요청마다 다시 로드하지 않음). 결과는 MJPG avi 라 **브라우저에서 바로 재생되지 않고 내려받아 재생**한다.
비로그인 응답 헤더 `X-Cutnkeep-Frames` · `X-Cutnkeep-Held` 는 CORS `expose_headers` 로 다른 도메인 프론트에서도 읽힌다.

---

## Console — 운영 콘솔 전용

콘솔(:5174)이 전체 작업을 보는 API. 인증이 없으므로 **서버 PC(loopback) 요청만 허용**,
다른 곳에서 오면 403 (`CONSOLE_ALLOW_REMOTE=true` 로 해제 — 앞단 접근 제어가 있을 때만).

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/v1/console/jobs?limit=50` | 전체 작업 최근 목록 (소유자 무관, 소유자 없는 옛 작업 포함) |
| `GET /api/v1/console/jobs/{job_id}` | 단건 — `before_url`/`after_url` 은 아래 콘솔 파일 경로 |
| `GET /api/v1/console/files/{job_id}/{before\|after}` | 작업 파일 (소유자 무관) |
| `GET /api/v1/console/learning/stats` | 학습 데이터 상태·출처·split 별 건수 + 학습 DB 모드 |
| `GET /api/v1/console/learning/samples?status=&source=&kind=&q=&limit=&offset=` | 학습 데이터 목록 (기본: 삭제 제외 전체) → `{items, total, limit, offset}` |
| `POST /api/v1/console/learning/samples/{id}/review` | `{"action": "approve"\|"reject"\|"reset", "answer"?: ParsedPrompt, "note"?}` — 승인 시 정답 수정 가능, 형식 오류 400 |
| `POST /api/v1/console/learning/samples/bulk` | `{"ids": [...], "action": "approve"\|"reject"}` → `{done, skipped}` |
| `DELETE /api/v1/console/learning/samples/{id}` | 삭제 + 원본 사이드카 파일 정리 → `{id, removed_files}` |
| `GET /api/v1/console/learning/samples/{id}/image` | 샘플 원본 이미지 (학습 데이터·업로드 폴더 안의 파일만) |

---

## DB

서비스 DB SQLite (`backend/data/cutnkeep.db`) + 학습 DB MariaDB (`feedbacks` · `learning_samples`) — [`docs/plan/DATABASE.md`](plan/DATABASE.md)
