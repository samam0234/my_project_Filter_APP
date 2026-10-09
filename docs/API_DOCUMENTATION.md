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
| `GET /api/v1/files/{job_id}/before` | 원본 — 사진 JPEG · 영상 원본 · GIF — **작업 소유자만** (그 외 404) |
| `GET /api/v1/files/{job_id}/after` | 결과 — 사진은 `remove_bg` 면 투명 PNG, 나머지 JPEG · 영상 mp4 · GIF — **작업 소유자만** |
| `GET /api/v1/files/{job_id}/webp` | GIF 배경 제거 결과의 **움직이는 WebP**(반투명 경계) — 있을 때만, **작업 소유자만** |
| `GET /api/v1/files/{job_id}/thumb` | 작업 기록 썸네일 — 영상은 결과 첫 프레임 JPEG(긴 변 480), 사진·GIF 는 결과 그대로 — **작업 소유자만** |

파일은 `backend/data/uploads/{job_id}/`(사진 · GIF) · `uploads/videos/{job_id}/`(영상)에 있으며 `FILE_RETENTION_HOURS` 뒤 `scripts/cleanup.py` 가 지운다.

---

## Jobs — 처리 이력

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/v1/jobs?limit=50` | **로그인 사용자 본인** 작업 최근 목록 — 사진 · 영상 · GIF (상한 200, 최신순) · 비로그인 401 |
| `GET /api/v1/jobs/{job_id}` | 본인 작업 단건 · 없거나 남의 작업이면 404 · 비로그인 401 |

```json
{
  "job_id": "…", "prompt": "왼쪽에서 두 번째 사람 지워줘", "status": "ok",
  "parsed_prompt": { "...": "..." }, "quality_score": 0.76,
  "before_url": "/api/v1/files/…/before", "after_url": "/api/v1/files/…/after",
  "backend": "yolo", "message": "ok", "feedback_saved": false,
  "created_at": "2026-09-30T03:59:10",
  "kind": "image", "thumb_url": "/api/v1/files/…/thumb"
}
```

`created_at` 은 UTC (시간대 표기 없음). `kind` = `image` · `video` · `gif` (예전 행은 `image`). GIF 배경 제거면 `webp_url` 도 있다. 영상 원본이 avi·mkv·mov 면 `before_url` 은 브라우저 재생용 mp4 미리 보기(원본 파일은 보관). 영상 · GIF 는 `quality_score` 가 0 이다 (사진 검증 단계를 거치지 않음).

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
| `POST /api/v1/video` | `multipart`: `file`(mp4/avi/webm/mov/mkv), `prompt`. 프레임 세그 후 **H.264 mp4**(원본 오디오 포함). **비로그인**은 첨부 응답만(저장 없음, 헤더 `X-Cutnkeep-Format` · `-Effect` · `-Intensity` · `-Frames` · `-Held`). **회원**은 `uploads/videos/{job_id}` 보관, JSON(`job_id` · `url` · `format` · `effect` · `intensity` · `frames` · `held`) |
| `GET /api/v1/video/{job_id}` | **본인만**. 비로그인·남의 영상이면 404 |

**회원 영상은 작업 기록에도 남는다** — `jobs` 에 `kind=video` 행(원본 · 결과 · 첫 프레임 `thumb.jpg`)이 생겨 `/jobs` · `/files/{job_id}/*` 로 다시 보고 받는다.
회원 응답 JSON 에는 `parsed_prompt` 도 담긴다. 요청 문장은 사진처럼 학습 데이터 검수 후보(`source=request`)로 모인다.

검출이 없는 프레임은 직전 마스크를 유지한다. **대상 지우기**는 영상을 두 번 읽어 다른 프레임에서 보인 배경판으로 메운다 (고정 카메라일 때, `VIDEO_REMOVE_MODE` — [video-removal-20261009.md](vaildates/video-removal-20261009.md)). 상한은 `VIDEO_MAX_FRAMES` · `VIDEO_MAX_SECONDS`.
프레임마다 selector(위치·순서·개수·색)로 인스턴스를 고른다 — 프레임 사이 추적은 없어 사람이 겹치거나 지나가면 선택이 바뀔 수 있다.
세그 모델은 프로세스 공용(요청마다 다시 로드하지 않음). 결과는 **H.264 mp4** 라 브라우저 `<video>` 로 바로 재생되고 어디서나 열린다.
OpenCV pip 휠에는 H.264 인코더가 없어(OpenH264 DLL 별도) 프레임은 MJPG 임시 avi 로 쓰고 **ffmpeg**(`imageio-ffmpeg` 번들 또는 PATH)로
libx264 · yuv420p · faststart 로 변환하며 원본의 첫 오디오 트랙을 aac 로 붙인다 (짧은 쪽에 맞춤).
ffmpeg 가 없거나 변환이 실패하면 webm(VP8) → MJPG avi(다운로드 전용) 순으로 자동 전환 — `format` 으로 구분, 처리 결과는 잃지 않는다.
`VIDEO_OUTPUT_FORMAT` 으로 시작 형식을 고를 수 있다 (`mp4` 기본 · `webm` · `avi`).

**블러 강도 보정:** 블러 커널은 픽셀 단위인데 사진은 긴 변 1280px 로 줄여 처리하는 반면 영상은 원본 해상도 그대로라, 1080p·4K 일수록 같은 강도가
거의 안 보였다(3840폭 선명도 6.8→5.4). 영상은 긴 변이 1280px 를 넘으면 그 비율만큼 강도를 키운다 (최대 255) — 응답의 `intensity` 는 요청 강도(보정 전).
업로드 검증: 확장자 + `video/*`(또는 octet-stream) + **내용 시그니처**(AVI·MP4/MOV·WebM/MKV). MIME 은 브라우저·OS 마다 달라(`.avi` → `video/avi`·`video/x-msvideo`) 시그니처가 기준이다.
비로그인 응답 헤더 `X-Cutnkeep-Frames` · `X-Cutnkeep-Held` 는 CORS `expose_headers` 로 다른 도메인 프론트에서도 읽힌다.

---

## GIF — 움직이는 GIF (작업실 GIF 탭)

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/gif` | `multipart`: `file`(.gif, 최대 `MAX_UPLOAD_SIZE_MB`), `prompt`. 프레임마다 영상과 같은 규칙(selector · 겹침 덜어내기 · 직전 마스크 유지 · 시간 스무딩)으로 처리해 다시 GIF 로 |

```json
{
  "job_id": "…", "status": "ok", "parsed_prompt": { "...": "..." },
  "before_url": "/api/v1/files/…/before", "after_url": "/api/v1/files/…/after",
  "frames": 120, "total": 300, "held": 2, "effect": "remove_bg", "transparent": true,
  "message": "프레임이 많아 앞 120개만 처리했어요 (전체 300개) · 검출이 없어 직전 모양을 유지한 프레임 2개",
  "saved": true
}
```

- **비로그인**: 저장하지 않음 — `after_url` 이 `data:image/gif;base64,…`, `before_url` 은 `null`, `saved=false`
- **회원**: `uploads/{job_id}/before.gif · after.gif` 보관, 작업 기록에 `kind=gif`
- 프레임 간격(duration) · 반복(loop)은 원본 그대로. 프레임 수는 `GIF_MAX_FRAMES`(기본 120)까지 — 넘으면 앞부분만 처리하고 `message` 로 알린다
- `remove_bg` 는 **투명 GIF**(1비트 투명, 알파 128 미만을 투명색으로). GIF 는 반투명이 없어 경계가 PNG 보다 거칠어 같은 프레임의
  **움직이는 WebP**(8비트 알파)도 만든다 → 응답 `webp_url` (비로그인은 `data:image/webp;base64,…`, 회원은 `/files/{id}/webp`). 그 밖의 효과는 불투명 GIF 만
- 검증: 확장자 `.gif` + MIME `image/gif`(또는 octet-stream) + 내용 시그니처(`GIF87a`/`GIF89a`)
- 처리 시간 참고: 480×360 · 10프레임 약 4초 (Docker, 모델 준비 후)

---

## 대상 마스크 처리 — 지정하지 않은 것이 섞이지 않게

선택한 인스턴스의 마스크에서 **같은 사진의 다른 인스턴스(다른 사람·개·가방·의자…)가 차지한 픽셀을 덜어낸다**(`MASK_EXCLUSIVE=subtract`).
경계 정제(GrabCut)와 CLAHE 대비 보정은 정답 주석 실험에서 섞임·경계·검출을 해쳐 기본으로 끈다(`MASK_GRABCUT` · `PREPROCESS_CLAHE`).
결과의 `meta.leak` 에 위험 신호가 담긴다: `conf_min`(고른 인스턴스의 최소 신뢰도 — 낮을수록 섞임·오선택 가능성이 높다),
`removed`(덜어낸 비율), `touching`·`crowd`(맞닿은 다른 인스턴스), `big_ratio`. 근거: [leak-diagnosis-20261008.md](vaildates/leak-diagnosis-20261008.md).

| 설정 | 기본 | 뜻 |
|------|------|-----|
| `MASK_EXCLUSIVE` | `subtract` | 다른 인스턴스 몫을 덜어내는 규칙 — `off` · `subtract` · `conf`(신뢰도 높은 쪽 소유) · `front`(앞사람 소유) |
| `MASK_OTHER_MIN_CONF` | 0.25 | 이보다 낮은 신뢰도로 잡힌 "다른 인스턴스"는 덜어내지 않는다 (헛검출 때문에 대상이 깎이지 않게) |
| `MASK_GRABCUT` | false | 경계 정제(GrabCut) — 켜면 이웃 조각을 끌어와 섞임이 늘었다 |
| `MASK_FORBID_REFINE` | false | GrabCut 을 켤 때 다른 인스턴스 구역을 금지 구역으로 둬 끌어오지 못하게 |
| `PREPROCESS_CLAHE` | false | 대비 보정 입력 — 켜면 검출·선택이 나빠졌다. 재시도는 반대쪽 입력 |
| `HARD_EXAMPLE_CONF` | 0 (끔) | 고른 인스턴스 최소 신뢰도가 이 값 미만이면 회원 요청을 학습 후보로 저장 |

## 인식 대상 (target)

| 종류 | 모델 | 대상 |
|------|------|------|
| 낱개 물체 | YOLO26m-seg (COCO 80) | person · dog · cat · car · bus · truck · bicycle · chair · bottle · cup · laptop · handbag … |
| 배경 덩어리 | SegFormer ADE20K (ONNX) | **building · sky · road · sidewalk · tree · grass · water · mountain · wall · floor · ceiling · ground · bridge · fence** |
| 그 밖 | Grounding DINO + SAM2 (`OPEN_VOCAB_ENABLED`, 로컬 전용 — 모델 `DINO_MODEL_ID`=IDEA-Research/grounding-dino-tiny · `SAM2_MODEL_ID`=facebook/sam2-hiera-tiny, 임계 `OPEN_VOCAB_BOX_THRESHOLD` 0.35 · `OPEN_VOCAB_TEXT_THRESHOLD` 0.25) | 자유 문구 |

- 한국어·동의어는 `prompt_spec.TARGET_ALIASES` 로 정규화 (건물·빌딩·집·아파트·house → `building`, 하늘 → `sky` …). LLM·휴리스틱 파서 모두 같은 어휘
- "건물" 같은 묶음은 소속 클래스(building · house · skyscraper · hovel)의 확률을 합쳐 판정, 연결된 덩어리마다 인스턴스로 내보내
  `왼쪽 건물` · `가장 큰 건물` 같은 위치·크기 선택이 그대로 동작
- 낱개와 섞인 요청("사람이랑 건물만 남겨")은 두 모델 결과를 합침 (`backend` = `yolo+segformer`)
- 모델 파일(`backend/models/segformer-ade.onnx`)이 없으면 이 경로만 꺼지고 기존 동작 (건물은 "찾지 못했습니다")
- 한계: 건물처럼 큰 영역을 **지우기**(`remove_object`)하면 인페인팅이 번져 보인다 — "남기고 배경 제거/블러"는 깔끔

## Console — 운영 콘솔 전용

콘솔(:5174)이 전체 작업·회원 데이터를 보는 API. 접근 규칙(`core/access.require_console`):

1. `CONSOLE_ADMINS` 에 있는 아이디로 로그인(`POST /api/v1/auth/login`, 같은 세션 쿠키) → 어디서든 허용
2. `CONSOLE_ALLOW_REMOTE=true` → 누구나 (하위 호환, 앞단 접근 제어가 있을 때만)
3. `CONSOLE_REQUIRE_LOGIN=false` 이고 서버 PC(loopback) → 로그인 없이 허용 (로컬 개발)

그 외: 비로그인 **401**, 관리자 아닌 회원 **403**. 배포에서는 `CONSOLE_REQUIRE_LOGIN=true` —
같은 서버의 리버스 프록시를 거치면 모든 요청이 127.0.0.1 로 보일 수 있다 (preflight 가 경고).
학습 데이터 검수 기록(`reviewed_by`)에는 `admin:{아이디}` 가 남는다.

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/v1/console/me` | `{via: "admin"\|"local"\|"open", username}` — 콘솔이 첫 진입에 호출, 401·403 이면 로그인 화면 |
| `GET /api/v1/console/system` | 런타임 스냅샷: `segmentation`(runtime not_loaded/ultralytics/onnx/stub) · `open_vocab` · `llm` · `batch`(Celery 일 때만 `redis_ok`) · `video` · `console` · `storage`(`areas` jobs/batches/videos 별 files·bytes·oldest_hours·expired_files, `disk`) · `preflight`. 모델을 새로 로드하지 않음 |
| `POST /api/v1/console/system/cleanup?dry_run=` | `FILE_RETENTION_HOURS` 지난 업로드 파일 삭제(`dry_run` 이면 집계만) → `{removed_files, freed_bytes, removed_dirs, dry_run, retention_hours}` |
| `GET /api/v1/console/users?q=&limit=&offset=` | 회원 목록 `{items, total, limit, offset}` — 작업·배치 수, 활성 세션, 잠김, `is_admin` (비밀번호 해시 없음) |
| `POST /api/v1/console/users/{id}/unlock` | 로그인 실패 잠금 해제 |
| `POST /api/v1/console/users/{id}/sessions/revoke` | 모든 세션 삭제 → `{id, revoked}` |
| `DELETE /api/v1/console/users/{id}` | 본문 `{"confirm": "아이디"}`. 계정·세션·작업·배치·영상·파일 삭제, 학습 샘플은 `user_id` 만 비움 → `{jobs, batches, videos, removed_dirs, learning_unlinked}`. 관리자·본인 400, 확인 아이디 불일치 400 |
| `GET /api/v1/console/jobs?limit=50` | 전체 작업 최근 목록 (소유자 무관, 소유자 없는 옛 작업 포함) — `kind` · `thumb_url` · `webp_url` 포함 |
| `GET /api/v1/console/batches?limit=50` | 전체 회원 배치 최근 목록 (상한 200) → `[{job_id, user_id, status, progress, total, completed, failed, message, prompt, created_at}]`. 회원 사진 보호를 위해 이미지 주소는 없다 |
| `GET /api/v1/console/jobs/{job_id}` | 단건 — `before_url`/`after_url` 은 아래 콘솔 파일 경로 |
| `GET /api/v1/console/files/{job_id}/{before\|after\|thumb\|webp}` | 작업 파일 (소유자 무관, 사진 · 영상 · GIF) |
| `GET /api/v1/console/learning/stats` | 학습 데이터 상태·출처·split 별 건수 + 학습 DB 모드 |
| `GET /api/v1/console/learning/samples?status=&source=&kind=&q=&limit=&offset=` | 학습 데이터 목록 (기본: 삭제 제외 전체) → `{items, total, limit, offset}` |
| `POST /api/v1/console/learning/samples/{id}/review` | `{"action": "approve"\|"reject"\|"reset", "answer"?: ParsedPrompt, "note"?}` — 승인 시 정답 수정 가능, 형식 오류 400 |
| `POST /api/v1/console/learning/samples/bulk` | `{"ids": [...], "action": "approve"\|"reject"}` → `{done, skipped}` |
| `DELETE /api/v1/console/learning/samples/{id}` | 삭제 + 원본 사이드카 파일 정리 → `{id, removed_files}` |
| `GET /api/v1/console/learning/samples/{id}/image` | 샘플 원본 이미지 (학습 데이터·업로드 폴더 안의 파일만) |

---

## DB

서비스 DB SQLite (`backend/data/cutnkeep.db`) + 학습 DB MariaDB (`feedbacks` · `learning_samples`) — [`docs/plan/DATABASE.md`](plan/DATABASE.md)
