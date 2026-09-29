# API Documentation

Base URL: `http://localhost:8000` · 대화형 문서: `/docs` (Swagger UI)
프론트(5173)·콘솔(5174) dev 서버는 Vite 프록시로 `/api`, `/health` 를 이 주소로 넘긴다.

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

파이프라인을 **동기**로 실행한 뒤 `jobs` 테이블에 저장한다. 로그인 상태면 작업을 사용자와 연결한다(`jobs.user_id`).
LLM 이 Ollama 일 때 요청당 약 15~30 초 (첫 요청은 모델 로드로 더 김).

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
  "feedback_saved": false
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
| `GET /api/v1/files/{job_id}/before` | 원본 JPEG |
| `GET /api/v1/files/{job_id}/after` | 결과 — `remove_bg` 는 투명 PNG, 나머지는 JPEG |

파일은 `backend/data/uploads/{job_id}/` 에 있으며 `FILE_RETENTION_HOURS` 뒤 `scripts/cleanup.py` 가 지운다.

---

## Jobs — 처리 이력

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/v1/jobs?limit=50` | 최근 목록 (상한 200, 최신순) |
| `GET /api/v1/jobs?mine=true` | 로그인 사용자의 작업만 (비로그인 401) |
| `GET /api/v1/jobs/{job_id}` | 단건. 없으면 404 |

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

`POST /api/v1/feedback` · JSON

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

## Batch (Phase 2 scaffold)

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/batch` | `multipart`: `files[]`(최대 `MAX_BATCH_SIZE`), `prompt` → 배치 등록만 (실제 처리 미구현) |
| `GET /api/v1/batch/{job_id}` | 상태·진행률. 없으면 `status: "not_found"` |

→ DB `batch_jobs`. 워커 구현은 `backend/app/tasks/batch_tasks.py` 하드코딩 구간.

---

## DB

로컬 SQLite (`backend/data/cutnkeep.db`) / 배포 MariaDB — [`docs/plan/DATABASE.md`](plan/DATABASE.md)
