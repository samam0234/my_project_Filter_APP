# 컷앤킵 기능 목록

지금 들어 있는 기능을 **빠짐없이 한 장에** 모은다. 기능마다 화면 · API · 주요 설정 · 코드 · 자세한 문서를 적는다.
기능을 새로 넣거나 바꾸면 여기부터 고친다. `tests/structure/test_docs_coverage.py` 가 다음 세 가지를 검사한다.
- 화면 경로와 미디어 API 가 이 문서에 있는지
- 엔드포인트가 API 문서에 있는지
- 설정이 `.env.example` 과 문서에 있는지

기준일: 2026-10-10 (`develop`) · 포트·DB·Docker 는 [`plan/CURRENT_STACK.md`](plan/CURRENT_STACK.md) · API 상세는 [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)

---

## 1. 사용자 앱 (frontend, :5173 · Docker :80)

🔒 = 로그인 회원 전용. 비로그인은 처리하고 바로 내려받기만 하며 서버에 남지 않는다.

| 기능 | 화면 | API | 설명 |
|------|------|-----|------|
| 홈 | `/` | `GET /jobs?limit=4` | 원본/결과 비교 데모(배경 제거 · 대상 지우기 · 배경 블러 탭, 손잡이 끌기·←/→), 예시 문장(누르면 작업실), 사용 순서, 최근 작업 |
| 사진 처리 | `/studio` | `POST /upload` | 1 사진 → 2 문장 → 3 처리. 진행 막대(해석 · 대상 찾기 · 효과), 해석 칩, 원본/결과 비교, 결과 저장(투명 PNG · JPEG) |
| GIF 처리 | `/studio?type=gif` | `POST /gif` | 움직이는 GIF 를 프레임마다 처리, 간격·반복 유지, 배경 제거는 투명 GIF + **WebP(부드러운 경계)**, 올릴 배경(밝은·어두운)을 고르면 GIF 경계도 부드럽게(매트), 120프레임까지 |
| 영상 처리 | `/video` | `POST /video` · `GET /video/{id}` | 최대 20초·80MB·긴 변 3840. H.264 mp4 + 오디오, 페이지에서 재생, 마지막 결과를 이 브라우저(IndexedDB)에 보관, 문장 고쳐 다시 처리 |
| 배치 🔒 | `/batch` | `POST /batch` · `GET /batch` · `GET /batch/{id}` · 항목 원본·결과 · zip | 같은 문장으로 최대 500장, 진행률 자동 갱신, 실패 항목 표시, 결과 zip |
| 작업 기록 🔒 | `/history` | `GET /jobs` | 사진 · 영상 · GIF 를 모아 보기 — 종류 필터 · 상태 필터 · 검색, 영상·GIF 배지와 썸네일 |
| 작업 상세 🔒 | `/jobs/:id` | `GET /jobs/{id}` · `GET /files/{id}/{before,after,thumb,webp}` | 결과 다시 보기(영상 재생), 해석 JSON 복사, 같은 문장으로 다시 작업 |
| 평가 · 정답 알려주기 🔒 | 작업실 · 작업 상세 | `POST /feedback` | 좋아요/싫어요, 해석이 틀렸으면 올바른 값을 골라 보냄 → 검수 후 학습 |
| 프롬프트 가이드 | `/guide` | — | 남기기 vs 지우기, 위치·크기·순서·개수·색 고르기, 예시, 한계, 보관 안내 |
| 회원가입 | `/signup` | `POST /auth/signup` | 입력 즉시 규칙 안내, **[필수] 만 14세 이상 · 약관 · 개인정보 처리방침 동의**(서버도 검사, 동의 시각 기록), 보관 기간·학습 이용 안내 |
| 로그인 · 로그아웃 | `/login` | `POST /auth/login` · `/logout` · `GET /auth/me` | `?next=` 로 돌아가기, HttpOnly 세션 쿠키 |
| 아이디 찾기 | `/find-id` | `POST /auth/find-id` | 가입 이메일로 아이디 발송 (있든 없든 같은 안내) |
| 비밀번호 찾기 | `/find-password` | `POST /auth/password/request` · `/reset` | 이메일 인증 코드 → 새 비밀번호 |
| 개인정보 처리방침 · 이용약관 | `/privacy` · `/terms` | — | 실제 동작과 같은 보관 기간 · 수집 항목 · 외부 전송, 운영자 정보는 빌드 인자 — [`guidance/legal.md`](guidance/legal.md) |
| 서버 상태 | 머리글 점 | `GET /health` | 30초마다, 초록 = 연결됨 |
| 디자인 | 전 화면 | — | 다크 테마, Pretendard, 낱말 단위 줄바꿈, 1024px 미만 펼침 메뉴, 키보드 초점 링 — [`vaildates/ui-design-20261008.md`](vaildates/ui-design-20261008.md) |

자세히: [`guidance/user-frontend.md`](guidance/user-frontend.md) · [`frontend/README.md`](../frontend/README.md) · 계정 [`guidance/auth.md`](guidance/auth.md)

## 2. 할 수 있는 요청 (문장 → 효과)

| 효과 | 예시 | 결과 |
|------|------|------|
| 남기고 배경 제거 `remove_bg` | "강아지만 남기고 배경 제거" | 투명 PNG · GIF/WebP |
| 배경 블러 `blur` (+ 강도) | "사람만 남기고 배경 블러 강도 40" | 대상 선명, 배경 흐림 (영상은 해상도에 맞춰 강도 보정) |
| 크롭 `crop` | "고양이만 크롭해줘" | 대상 주변으로 자름 |
| 대상 지우기 `remove_object` | "오른쪽 사람 지워줘" | 사진은 **LaMa** 로 주변 무늬를 이어 그림, 영상·GIF 는 다른 프레임에서 보인 **실제 배경**으로 메움(고정 카메라) |
| 특정 대상 고르기 `selector` | "맨 앞 빨간 안전모 쓴 사람", "왼쪽에서 두 번째", "사람 2명", "가장 큰 개" | 위치 · 순서 · 개수 · 크기 · 색/부위 |
| 대상 어휘 | 사람 · 동물 · 탈것 · 물건 등 COCO 80종 + 건물 · 하늘 · 도로 · 나무 등 14종 (+ 자유 문구는 오픈 보캐브) | 한국어 · 동의어 별칭 |

규격 정본: `backend/app/services/prompt_spec.py` · 자세히: [`guidance/llm-and-vision.md`](guidance/llm-and-vision.md)

## 3. 처리 엔진 (backend)

| 기능 | 코드 | 주요 설정 | 근거 · 문서 |
|------|------|-----------|-------------|
| 파이프라인 (LangGraph) | `workflows/` | `PRELOAD_MODELS` | 해석 → 전처리 → 세그 → 검증·재시도 → 효과 → 피드백 — [`WORKFLOW.md`](WORKFLOW.md) |
| 문장 해석 LLM | `services/prompt_llm.py` | `LLM_PROVIDER`(ollama · lora · openai · gemini) · `LLM_FALLBACK` | 기본 Ollama `gemma4:e4b` |
| 키워드 파서 | `services/heuristic_targets.py` | — | LLM 이 꺼져도 동작, 역할 규칙(남길 것 · 뺄 것 · 지울 것) |
| 해석 체인 (LangChain) | `services/prompt_chain.py` | `PROMPT_CHAIN=langchain` · `PROMPT_VOTES` | LLM 답과 키워드 파서가 다르면 다수결 — 처음 본 문장 86.7→96.7% |
| RAG 예시 | `services/prompt_rag.py` | `PROMPT_RAG_*` | 승인된 교정 문장을 LLM 예시로, 30초 안에 반영 |
| 해석 혼합 (선택) | `services/prompt_chain.py` | `PROMPT_SECOND_OPINION` | LoRA 먼저, 키워드 파서와 갈릴 때만 다른 provider(Ollama) — 253문장 91.3% · 3.0초 (기본 체인 85.4% · 6.9초) — [`vaildates/parser-compare-20261009.md`](vaildates/parser-compare-20261009.md) |
| LoRA 해석 모델 | `services/prompt_lora.py` · `training/lora/` | `LLM_PROVIDER=lora` | Qwen2.5-1.5B 어댑터 — [`vaildates/lora-selector-20261009.md`](vaildates/lora-selector-20261009.md) (조합형 + 선택자 문장, 283문장 94.7% · 1.0초/문장 GPU) |
| 낱개 물체 세그 | `services/segmentation.py` | `YOLO_MODEL_PATH` · `SEG_PREFER_ONNX` · `SEG_IMGSZ` · `SEG_NMS_IOU` (Docker 빌드 인자 `SEG_RUNTIME`) | YOLO26m-seg (.pt / ONNX) |
| 배경 덩어리 세그 | `services/stuff_segmentation.py` | `STUFF_*` | SegFormer ADE20K ONNX — [`vaildates/stuff-segmentation-20261008.md`](vaildates/stuff-segmentation-20261008.md) |
| 오픈 보캐브 | Grounding DINO + SAM2 | `OPEN_VOCAB_*` · `DINO_MODEL_ID` · `SAM2_MODEL_ID` | 기본 꺼짐, 로컬 가중치 — [`vaildates/open-vocab-20261007.md`](vaildates/open-vocab-20261007.md) |
| 인스턴스 고르기 | `services/instance_selector.py` | — | 위치 · 순서 · 개수 · 크기 · 색 |
| 섞임 막기 (겹침 덜어내기) | `services/mask_exclusion.py` | `MASK_EXCLUSIVE` · `MASK_OTHER_MIN_CONF` · `MASK_GRABCUT` · `MASK_FORBID_REFINE` · `PREPROCESS_CLAHE` | 지정하지 않은 대상이 섞이지 않게 — [`vaildates/leak-diagnosis-20261008.md`](vaildates/leak-diagnosis-20261008.md) |
| 검증 · 재시도 | `services/validator.py` · `workflows/edges.py` | — | ok · fallback · failed, 반대쪽 입력 + 낮은 신뢰도로 한 번 더, 더 나은 쪽 채택 |
| 효과 · 경계 | `services/effects.py` | — | 업스케일 · 안티앨리어싱 · 깃털 알파 — [`vaildates/edge-tuning-20261008.md`](vaildates/edge-tuning-20261008.md) |
| 대상 지우기 메우기 | `services/inpaint.py` | `INPAINT_ENGINE` · `INPAINT_MODEL_PATH` | LaMa ONNX(없으면 Telea) — [`vaildates/inpaint-20261009.md`](vaildates/inpaint-20261009.md) |
| 모델 자동 받기 | `services/model_fetch.py` · `scripts/fetch_models.py` | `MODEL_AUTO_DOWNLOAD` | 없는 LaMa 를 기동 시 백그라운드로 받고 SHA-256 확인, 생기면 바로 LaMa 로 |
| 영상 | `services/video_processor.py` | `VIDEO_*` | 프레임마다 같은 규칙(`FrameRenderer`), 광학 흐름 스무딩, mp4 변환, avi 등 원본 미리 보기 |
| 영상 · GIF 지우기 | `services/video_inpaint.py` | `VIDEO_REMOVE_MODE` | 다른 프레임에서 보인 배경판으로 메우고 안 보인 곳만 LaMa 한 번 (고정 카메라 · 카메라가 움직이면 프레임 맞춤), 맞출 수 없거나 그 프레임과 배경이 안 맞으면 Telea, 배경판은 시간 중앙값 + 밝기 맞춤 — [`vaildates/video-removal-20261009.md`](vaildates/video-removal-20261009.md) · [`video-removal-pan-20261009.md`](vaildates/video-removal-pan-20261009.md) · 실제 영상 [`davis-real-video-20261010.md`](vaildates/davis-real-video-20261010.md) |
| 영상 · GIF 대상 추적 | `services/instance_tracker.py` | `VIDEO_TRACK_INSTANCES` | "왼쪽 사람"처럼 위치 · 순서 · 개수로 고른 대상을 첫 프레임에서 고른 그 사람으로 끝까지 — 서로 지나가도 유지(YOLO 99.4%), 중복 검출 · 합쳐짐 · 오래 가려짐 대비 — [`vaildates/video-tracking-20261009.md`](vaildates/video-tracking-20261009.md) · [`video-tracking-hard-20261009.md`](vaildates/video-tracking-hard-20261009.md) · 실제 영상 [`davis-real-video-20261010.md`](vaildates/davis-real-video-20261010.md) (맞은 비율 72.8→92.1%) |
| GIF | `services/gif_processor.py` | `GIF_MAX_FRAMES` · `GIF_MAX_PIXELS` | 투명 GIF + 움직이는 WebP |
| 배치 | `routers/batch.py` · `tasks/batch_tasks.py` | `BATCH_USE_CELERY` | 최대 500장, 한 장씩 처리, Celery 는 선택 |

## 4. 학습 루프

| 기능 | 어디서 | 설명 |
|------|--------|------|
| 피드백 수집 | `POST /feedback` → 학습 DB + `data/feedback/` | 좋아요 · 싫어요 · 정답 알려주기 |
| 회원 요청 후보 | 사진 · 영상 · GIF 처리 시 | 요청 문장 + 해석을 검수 후보로 (`LEARNING_COLLECT_REQUESTS`) |
| 어려운 사례 수집 | LangGraph `feedback_collector` | `HARD_EXAMPLE_CONF` (기본 꺼짐) |
| 콘솔 검수 | 콘솔 "학습 데이터" | 승인 · 정답 고쳐서 승인 · 거절 · 일괄 |
| GPU 서버 (CUDA) | `docker-compose.gpu.yml` · `backend/Dockerfile` | `TORCH_INDEX` · `LLM_LORA` · `GPU_LLM_PROVIDER` · `GPU_LLM_FALLBACK` · `LORA_BASE_DIR` | CUDA torch 이미지, 문장 해석 LoRA(문장당 1.85초 GPU) · 세그 GPU — [`guidance/gpu-deploy.md`](guidance/gpu-deploy.md) |
| 운영 `.env` 만들기 | `scripts/make_prod_env.py` | `CNK_SMTP_PASSWORD`(환경 변수) | 운영 값 · 새 비밀 값(SECRET_KEY · DB 비밀번호)을 채운 `.env.production` + 기동 전 점검 — [`DEPLOYMENT.md`](DEPLOYMENT.md) |
| 배포 리허설 | `scripts/deploy_check.py` · `scripts/models_bundle.py` | — | 실서버를 밖 · 안에서 점검(실패 시 종료 코드 1, `--gpu` · `--env-file`), git 밖 모델을 묶어 옮기고 체크섬 대조 — [`DEPLOYMENT.md`](DEPLOYMENT.md) |
| 의존성 취약점 점검 | `.github/workflows/ci.yml` | — | push 마다 · 매주 월요일 `pip-audit`, 프론트 · 콘솔 `npm audit --omit=dev` — [`guidance/security.md`](guidance/security.md) 5절 |
| 실패 사진 보관 기간 | `services/feedback_images.py` | `FEEDBACK_IMAGE_RETENTION_DAYS` | 처리 실패 · 인식 불확실한 회원 요청의 원본 사진을 기간 뒤 자동 삭제, 계정 삭제 시 바로 삭제 · 기록은 익명 — 처리방침에 같은 일수 표시 |
| 세그 실패 사진 라벨링 | `scripts/seg_labeling.py` | `HARD_EXAMPLE_CONF` (수집) | 실패 · 싫어요 사진을 큰 모델 초벌 라벨과 함께 Label Studio 용으로 내보내고, 고친 라벨을 학습 전에 검사 |
| 세그 모델 재학습 | `scripts/retrain_yolo.py` | 어려운 사례 수집 · 이어 학습 · 섞임 평가 + mAP 판정 · 배포 (`--deploy`, `--extra` 직접 라벨링 사진) — [`vaildates/yolo-retrain-20261009.md`](vaildates/yolo-retrain-20261009.md) (COCO 만으로는 불채택) |
| LoRA 재학습 | `scripts/retrain_lora.py` | 증강 · 학습 · 평가셋 7개(승인 val 포함) 판정 · 배포 (`--deploy`), 조합형 시드 `training/lora/seed/build_compositional.py` |
| YOLO 학습 | `training/` | 데이터 · 학습 · `apply_best.py` 로 배포 |
| 의사 라벨 | `scripts/pseudo_labeling.py` | 오픈 보캐브로 라벨 후보 |

전체 흐름: [`guidance/learning-loop.md`](guidance/learning-loop.md)

## 5. 운영 콘솔 (console, :5174)

| 메뉴 | API | 설명 |
|------|-----|------|
| 로그인 | `GET /console/me` | 관리자(`CONSOLE_ADMINS`) 로그인 또는 서버 PC(`CONSOLE_REQUIRE_LOGIN=false`) |
| 대시보드 | `/health` · `/console/jobs` | 상태 · 집계 · 최근 작업 |
| 작업 목록 | `GET /console/jobs` · `/console/files/{id}/*` | 전체 작업(사진 · 영상 · GIF 표시) |
| 배치 현황 | `GET /console/batches` | 전체 회원 배치 (이미지 비노출) |
| 학습 데이터 | `/console/learning/*` | 검수 · 통계 · 원본 이미지 |
| 회원 관리 | `/console/users*` | 검색 · 잠금 해제 · 세션 끊기 · 계정 삭제(파일 포함) |
| 시스템 | `GET /console/system` · `POST /console/system/cleanup` | 설정 점검 · 런타임 · 마스크/지우기 엔진 · 저장 공간 · 정리 |
| 바로가기 | — | 사용자 앱 · Swagger · Health |

자세히: [`guidance/console-admin.md`](guidance/console-admin.md)

## 6. 보안 · 운영

| 기능 | 설정 | 설명 |
|------|------|------|
| 계정 보안 | `LOGIN_MAX_FAILURES` · `LOGIN_LOCK_MINUTES` · `SESSION_TTL_HOURS` · `SESSION_COOKIE_SECURE` · `SECRET_KEY` | scrypt 해시, 연속 실패 잠금, HttpOnly 세션, 이메일 코드 재설정 |
| HTTPS | `docker-compose.https.yml` · `DOMAIN` · `ACME_EMAIL` | Caddy 가 인증서 자동 발급·갱신, http→https, Secure 쿠키 · HSTS — [`guidance/https-deploy.md`](guidance/https-deploy.md) |
| 메일 | `SMTP_*` · `SMTP_SSL` | 587(STARTTLS) · 465(SSL), 개발용 Mailpit(프로필 mail), `scripts/send_test_mail.py` — [`guidance/auth.md`](guidance/auth.md) |
| 접근 정책 | — | 결과 파일 · 기록은 본인만(404), 비로그인은 저장하지 않음 |
| 속도 제한 | `UPLOAD_RATE_*` · `TRUSTED_PROXIES` | 비로그인 IP 별 · 회원 계정별, nginx 뒤에서도 사람마다 |
| 업로드 검증 | `MAX_UPLOAD_SIZE_MB` · `MAX_IMAGE_PIXELS` · `GIF_MAX_PIXELS` · `VIDEO_MAX_SIDE` | 확장자 · MIME · 시그니처 · 해상도(압축 폭탄) |
| 보안 헤더 | `frontend/nginx.conf` | CSP · X-Frame-Options · nosniff · Referrer · Permissions, 버전 숨김 |
| 포트 제한 | `BIND_HOST` · `BACKEND_PORT` | 공개는 :80, 나머지는 127.0.0.1 |
| 자동 정리 | `FILE_RETENTION_HOURS` · `FILE_CLEANUP_MINUTES` | 24시간 지난 업로드를 매시간 삭제 (`.gitkeep` 보호) |
| 서비스 DB | `DOCKER_DB_DIALECT` · `SERVICE_DB_IMPORT_FROM` | Docker 는 MariaDB(처음 전환 시 옛 SQLite 자동 이전), 호스트 개발은 SQLite |
| MariaDB 백업 | `MARIADB_BACKUP_HOURS` · `MARIADB_BACKUP_KEEP_DAYS` | `mariadb-backup` 서비스가 서비스 + 학습 DB 를 매일 덤프, 7일 보관, 복구 확인됨 |
| SQLite 백업 (호스트) | `DB_BACKUP_HOURS` · `DB_BACKUP_KEEP` | 온라인 백업, 임시 이름으로 쓰고 끝나면 이름 변경, 깨진 백업은 버림 |
| DB 손상 감지 | — | 기동 시 `quick_check`, 호스트/Docker DB 파일 분리 |
| 배포 설정 점검 | `APP_ENV` · `PREFLIGHT_STRICT` | production 에서 위험한 기본값이면 기동 거부 |
| 로그 | `LOG_DIR` · `LOG_RETENTION_DAYS` | `backend/logs/app_YYYY-MM-DD.log`, 14일 |

점검표: [`guidance/security.md`](guidance/security.md) · DB: [`plan/DATABASE.md`](plan/DATABASE.md)

## 7. 실행 · 인프라

| 구성 | 설명 |
|------|------|
| 로컬 | backend `uvicorn`(:8000) · frontend Vite(:5173) · console Vite(:5174) — [`../RUN.md`](../RUN.md) |
| Docker (`-p cut_and_keep`) | frontend(nginx :80) · backend · MariaDB · Redis · Adminer · celery_worker(프로필 phase2) — [`guidance/docker-run.md`](guidance/docker-run.md) |
| 모델 파일 (git 밖) | `backend/models/` — YOLO · SegFormer · LaMa · LoRA ([`backend/models/README.md`](../backend/models/README.md)) |
| 테스트 | 백엔드 pytest · 프론트/콘솔 vitest · 문서 등록 검사 — [`plan/TESTING.md`](plan/TESTING.md) |
| 실험 · 평가 | `scripts/experiments/` — 결과는 [`vaildates/README.md`](vaildates/README.md) |
