"""중앙 설정 (Pydantic Settings). 경로·모델명은 여기서만 관리.

환경변수 / .env 로 덮어쓴다 (alias = 환경변수 이름).
경로는 두 기준으로 나눠 절대 경로로 해석한다.
  - 서비스 런타임 (backend/ 기준): uploads, SQLite DB, 앱 로그, 서빙 중인 모델
  - 학습 공유 자산 (저장소 루트 기준): feedback, pseudo_labels
Docker 에서는 둘 다 /app 이며, compose 마운트로 같은 역할 분리를 유지한다.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _backend_root() -> Path:
    """서비스 런타임 루트: 로컬 …/backend, Docker /app."""
    return Path(__file__).resolve().parents[2]


def _project_root() -> Path:
    """
    학습 공유 자산 루트 해석.
    - 로컬 모노레포: 저장소 루트 (…/CutNKeep)
    - Docker (backend 전용 이미지): 작업 디렉터리 (/app)
    """
    backend_root = _backend_root()
    repo_candidate = backend_root.parent
    # 모노레포 신호: frontend 또는 docs 폴더가 있으면 저장소 루트로 간주
    if (repo_candidate / "frontend").is_dir() or (repo_candidate / "docs").is_dir():
        return repo_candidate
    return backend_root



class Settings(BaseSettings):
    """앱 전역 설정 객체. get_settings() 로 싱글톤 사용."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",  # 알 수 없는 env 키는 무시
    )

    # --- 런타임 ---
    # 【수동·.env】 APP_ENV / DEBUG
    # 조건: 로컬=development+true, 배포=production+false 권장
    # 기능: 로그 레벨·개발 편의. SECRET_KEY 는 배포 시 반드시 긴 난수로 교체
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY")
    # APP_ENV=production 에서 위험한 설정(기본 SECRET_KEY·DEBUG·비보안 쿠키·SMTP 없음 등)이면 기동 거부
    # (core/preflight.py). false 면 경고 로그만
    preflight_strict: bool = Field(default=True, alias="PREFLIGHT_STRICT")
    # 업로드(LLM + GPU) 분당 허용 횟수 — 비로그인은 IP, 회원은 계정 기준. 0 = 제한 없음 (core/ratelimit.py)
    upload_rate_guest_per_min: int = Field(default=6, alias="UPLOAD_RATE_GUEST_PER_MIN")
    upload_rate_member_per_min: int = Field(default=20, alias="UPLOAD_RATE_MEMBER_PER_MIN")

    # --- 업로드 제한 ---
    # 【수동·.env】 MAX_UPLOAD_SIZE_MB / ALLOWED_MIME_TYPES
    # 조건: 프론트 ImageUploader maxSize 와 동일하게 맞출 것 (기본 20MB)
    # 기능: 보안 검증 통과 기준. webp 제외 시 프론트 accept 도 같이 수정
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    allowed_mime_types: str = Field(
        default="image/jpeg,image/png,image/webp",
        alias="ALLOWED_MIME_TYPES",
    )

    # --- 서비스 런타임 경로 (상대 경로는 backend/ 기준) ---
    # 【수동·필수】 YOLO_MODEL_PATH — 지금 서빙 중인 활성 모델 (backend/models/)
    # 조건:
    #   1) 서비스 본선은 **세그** 가중치 (yolo26m-seg.pt 또는 .onnx — 2026-10-06 s→m, docs/plan/YOLO26M_DEFAULT.md), git 에 안 올라감
    #   2) 없으면 segmentation 이 stub 타원 마스크로 동작 (데모용)
    # 기능: Segmentor 가 Ultralytics/ONNX 로 로드하는 유일한 경로 설정
    # 배포: 루트 models/(원본·후보 보관소) 또는 학습 best.pt
    #       → training/yolo/apply_best.py 가 backend/models/ 로 복사
    # 【수동】 SEG_PREFER_ONNX — YOLO_MODEL_PATH 가 .onnx 일 때 ultralytics 가 설치돼 있어도 onnxruntime 으로 추론
    # (torch 없이 CPU 에서 가볍게. 경량 Docker 이미지는 ultralytics 가 없어 자동으로 이 경로). 검증: scripts/experiments/onnx_vs_pt.py
    seg_prefer_onnx: bool = Field(default=False, alias="SEG_PREFER_ONNX")
    yolo_model_path: str = Field(
        default="models/yolo26m-seg.pt",
        alias="YOLO_MODEL_PATH",
    )
    # 【수동】 업로드 before/after — FILE_RETENTION_HOURS 뒤 scripts/cleanup.py 가 정리
    upload_dir: str = Field(default="data/uploads", alias="UPLOAD_DIR")
    # 【수동】 백엔드 파일 로그 (일자별 회전)
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    log_retention_days: int = Field(default=14, alias="LOG_RETENTION_DAYS")

    # --- 학습 공유 경로 (상대 경로는 저장소 루트 기준) ---
    # backend 가 기록하고 training/·scripts/ 가 읽는 학습 재료
    feedback_dir: str = Field(default="data/feedback", alias="FEEDBACK_DIR")
    pseudo_label_dir: str = Field(
        default="data/pseudo_labels",
        alias="PSEUDO_LABEL_DIR",
    )

    # --- LLM: ollama(기본) | openai | gemini | heuristic ---
    # 참고: docs/plan/AI_MODEL_STRATEGY.md

    # =============================================================================
    # [이미 구현된 구간 · 바이브] LLM Settings 필드 정의
    # -----------------------------------------------------------------------------
    # HTTP 호출은 services/prompt_llm.py, 분기는 workflows/nodes.prompt_analyzer.
    # [규칙] .env alias 일치. 시크릿 커밋 금지. 새 provider 시 Field+prompt_llm 동시.
    # =============================================================================
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_base_url: str | None = Field(
        default="http://localhost:11434",
        alias="LLM_BASE_URL",
    )
    ollama_model: str = Field(default="gemma4:e4b", alias="OLLAMA_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    # 【수동·튜닝】 LLM_TIMEOUT_SECONDS — Ollama 첫 호출은 모델 로드로 느릴 수 있음
    # 초과 시 휴리스틱 fallback 이므로 너무 길면 업로드 응답이 늦어진다
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")
    # 【수동】 LLM_FALLBACK — 기본 provider 가 LLMError 일 때 한 번 더 시도 (기본 로컬 Ollama).
    # 같은 값이거나 heuristic/빈 값이면 건너뛴다. 둘 다 실패하면 휴리스틱.
    llm_fallback: str = Field(default="ollama", alias="LLM_FALLBACK")
    # 【수동·선택】 LLM_PROVIDER=lora — training/lora 로 학습한 어댑터를 transformers 로 서빙
    # 경로는 backend/ 기준. 베이스는 HF 형식 폴더(config.json + safetensors), 어댑터는 서빙용 복사본
    lora_base_model: str = Field(default="", alias="LORA_BASE_MODEL")
    lora_adapter_path: str = Field(default="models/lora", alias="LORA_ADAPTER_PATH")
    # 【수동·튜닝】 프롬프트 해석 RAG — 비슷한 정답 예시(사용자 교정·좋아요·시드)를 LLM 지시문에 붙임
    # (ollama · openai · gemini 에만 적용. lora 는 학습 템플릿이 고정이라 제외)
    prompt_rag_enabled: bool = Field(default=True, alias="PROMPT_RAG_ENABLED")
    # 기본은 운영 콘솔에서 승인된 교정·좋아요·회원 요청만. 시드(seed)는 고정 규칙과 겹쳐 평가에서 정확도를 낮춤
    # (eval 40건: 없음 95.0% → 시드 포함 90.0~92.5%, docs/guidance/llm-and-vision.md)
    prompt_rag_sources: str = Field(default="correction,like,request", alias="PROMPT_RAG_SOURCES")
    prompt_rag_top_k: int = Field(default=3, alias="PROMPT_RAG_TOP_K")
    prompt_rag_min_score: float = Field(default=0.6, alias="PROMPT_RAG_MIN_SCORE")
    prompt_rag_refresh_seconds: float = Field(default=30.0, alias="PROMPT_RAG_REFRESH_SECONDS")
    # 저장소 루트 기준 (Docker 이미지에는 training/ 이 없어 피드백만 사용)
    prompt_rag_seed_file: str = Field(default="training/lora/seed/train.jsonl", alias="PROMPT_RAG_SEED_FILE")

    # 【수동】 PRELOAD_MODELS — 기동 직후 세그 모델을 백그라운드로 미리 로드 (첫 요청 20초+ 지연 제거)
    preload_models: bool = Field(default=True, alias="PRELOAD_MODELS")

    # --- 계정 (로그인 · 회원가입 · 아이디/비밀번호 찾기) ---
    # 【수동·배포】 SESSION_COOKIE_SECURE — HTTPS 배포 시 true (로컬 http 는 false 여야 쿠키 저장)
    session_cookie_name: str = Field(default="cnk_session", alias="SESSION_COOKIE_NAME")
    session_ttl_hours: int = Field(default=168, alias="SESSION_TTL_HOURS")  # 7일
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    # 【수동·보안】 운영 콘솔 API(/api/v1/console/*)는 인증이 없어 기본적으로 이 PC(loopback)에서만 허용.
    # 원격 허용은 앞단에서 접근 제어(VPN·방화벽·리버스 프록시 인증)를 한 경우에만 true
    console_allow_remote: bool = Field(default=False, alias="CONSOLE_ALLOW_REMOTE")
    # 【수동·보안】 운영 콘솔 관리자 아이디 (쉼표 구분). 이 계정으로 로그인하면 어디서든 콘솔 API 사용 가능
    console_admins: str = Field(default="", alias="CONSOLE_ADMINS")
    # 【수동·배포】 true 면 서버 PC(loopback)여도 관리자 로그인 필수. 같은 서버의 리버스 프록시(nginx 등)를 거치면
    # 모든 요청이 127.0.0.1 로 보일 수 있어 배포에서는 true 권장
    console_require_login: bool = Field(default=False, alias="CONSOLE_REQUIRE_LOGIN")
    # 【수동·튜닝】 로그인 잠금 · 비밀번호 재설정 코드
    login_max_failures: int = Field(default=5, alias="LOGIN_MAX_FAILURES")
    login_lock_minutes: int = Field(default=10, alias="LOGIN_LOCK_MINUTES")
    auth_code_ttl_minutes: int = Field(default=10, alias="AUTH_CODE_TTL_MINUTES")
    auth_code_max_attempts: int = Field(default=5, alias="AUTH_CODE_MAX_ATTEMPTS")
    auth_code_resend_seconds: int = Field(default=60, alias="AUTH_CODE_RESEND_SECONDS")

    # --- 메일 (아이디 찾기 · 비밀번호 재설정 코드 발송) ---
    # 【수동·배포 필수】 SMTP_HOST 가 비어 있으면 메일을 보내지 않고 서버 로그에만 남긴다 (개발용).
    # 코드는 절대 API 응답으로 돌려주지 않는다.
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="Cut & Keep <no-reply@cutnkeep.local>", alias="SMTP_FROM")
    smtp_starttls: bool = Field(default=True, alias="SMTP_STARTTLS")


    # --- 큐 / 파일 수명 (Phase 2 배치에서 사용) ---
    # 【수동·Phase2】 REDIS_URL — compose 호스트 포트는 6380 매핑 주의
    # FILE_RETENTION_HOURS: scripts/cleanup.py 와 동일 env 사용
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    # 【수동·Phase2】 true 이고 celery 가 설치돼 있으면 배치를 Redis 워커로 보낸다.
    # 기본 false: API 프로세스의 BackgroundTasks 가 한 장씩 처리 (compose 기본 up 과 동일).
    batch_use_celery: bool = Field(default=False, alias="BATCH_USE_CELERY")
    file_retention_hours: int = Field(default=24, alias="FILE_RETENTION_HOURS")
    # 【수동·Phase2】 닫힌 어휘(YOLO names)에 없는 대상만 Grounding DINO+SAM2.
    # 가중치·torch 가 없으면 업로드는 YOLO/ONNX/stub 으로 계속된다. 기동 중 다운로드 없음.
    open_vocab_enabled: bool = Field(default=False, alias="OPEN_VOCAB_ENABLED")
    dino_model_id: str = Field(
        default="IDEA-Research/grounding-dino-tiny",
        alias="DINO_MODEL_ID",
    )
    sam2_model_id: str = Field(default="facebook/sam2-hiera-tiny", alias="SAM2_MODEL_ID")
    # Grounding DINO 박스·문구 임계값. YOLO 의 MIN_CONFIDENCE 와 점수 분포가 달라 따로 둔다
    # (docs/vaildates/open-vocab-20261007.md — COCO 정답으로 측정해 고른 값).
    open_vocab_box_threshold: float = Field(default=0.35, ge=0.05, le=0.95, alias="OPEN_VOCAB_BOX_THRESHOLD")
    open_vocab_text_threshold: float = Field(default=0.25, ge=0.05, le=0.95, alias="OPEN_VOCAB_TEXT_THRESHOLD")
    # 【수동·튜닝】 세그 입력 크기·NMS — 0 이면 모델 기본값(640, 0.7). 크게 하면 작은 사람·붙은 사람이 나뉘지만 느려진다
    seg_imgsz: int = Field(default=0, ge=0, le=2048, alias="SEG_IMGSZ")
    seg_nms_iou: float = Field(default=0.0, ge=0.0, lt=1.0, alias="SEG_NMS_IOU")
    # 【수동·튜닝】 지정하지 않은 사람·동물·물체가 대상에 붙어 남는 것을 막는다 (services/mask_exclusion.py, docs/vaildates/leak-*.md)
    #   MASK_EXCLUSIVE   : off | subtract | conf | front — 다른 인스턴스가 차지한 픽셀을 대상에서 덜어내는 규칙
    #   MASK_FORBID_REFINE: true 면 경계 정제(GrabCut)가 다른 인스턴스 구역을 대상으로 끌어오지 못하게 한다
    mask_exclusive: Literal["off", "subtract", "conf", "front"] = Field(default="subtract", alias="MASK_EXCLUSIVE")
    mask_forbid_refine: bool = Field(default=False, alias="MASK_FORBID_REFINE")
    # 경계 정제(GrabCut)와 대비 보정(CLAHE) — 정답 주석 비교 실험에서 둘 다 켜면 오히려 손해였다
    # (섞임 6.3→4.6%, 경계 F 0.52→0.61, IoU 0.77→0.81, 선택 정확 0.89→0.91 — docs/vaildates/leak-diagnosis-20261008.md).
    # 질감이 가는 머리카락 결은 GrabCut 이 조금 더 선명할 수 있어 옵션으로 남긴다.
    mask_grabcut: bool = Field(default=False, alias="MASK_GRABCUT")
    preprocess_clahe: bool = Field(default=False, alias="PREPROCESS_CLAHE")
    mask_other_min_conf: float = Field(default=0.25, ge=0.0, le=1.0, alias="MASK_OTHER_MIN_CONF")
    # 【수동】 배경 덩어리(건물·하늘·도로·나무…) 의미 분할 — SegFormer(ADE20K) ONNX. YOLO(COCO)에 없는 대상용.
    # 파일은 scripts/export_stuff_onnx.py 로 만든다. 없으면 이 경로만 꺼지고 나머지는 그대로 동작한다.
    stuff_seg_enabled: bool = Field(default=True, alias="STUFF_SEG_ENABLED")
    stuff_model_path: str = Field(default="models/segformer-ade.onnx", alias="STUFF_MODEL_PATH")
    stuff_min_prob: float = Field(default=0.5, gt=0.0, lt=1.0, alias="STUFF_MIN_PROB")  # 묶음 확률 임계
    stuff_use_gpu: bool = Field(default=False, alias="STUFF_USE_GPU")  # onnxruntime-gpu 가 있을 때만 의미 있음
    # 【수동】 영상 업로드. 비로그인은 응답으로만 받고 디스크에 남기지 않는다.
    video_max_upload_mb: int = Field(default=80, alias="VIDEO_MAX_UPLOAD_MB")
    video_max_frames: int = Field(default=240, alias="VIDEO_MAX_FRAMES")
    video_max_seconds: float = Field(default=20.0, alias="VIDEO_MAX_SECONDS")
    # mp4(H.264+오디오, ffmpeg 필요) | webm(VP8) | avi(MJPG, 다운로드 전용·가장 빠름). 못 만들면 mp4 → webm → avi 순으로 내려간다
    video_output_format: Literal["mp4", "webm", "avi"] = Field(default="mp4", alias="VIDEO_OUTPUT_FORMAT")
    # 영상 마스크 깜빡임 줄이기 — flow(광학 흐름으로 이전 마스크를 옮겨 섞음) | ema(그냥 섞음, 움직이면 꼬리) | off
    # 비중 = 현재 프레임 몫. 0.5 이상이면 이진 마스크라 효과가 없다 (docs/vaildates/edge-tuning-20261008.md)
    video_temporal_smoothing: Literal["flow", "ema", "off"] = Field(default="flow", alias="VIDEO_TEMPORAL_SMOOTHING")
    video_smoothing_weight: float = Field(default=0.3, gt=0.0, lt=0.5, alias="VIDEO_SMOOTHING_WEIGHT")

    # 【수동】 CORS_ORIGINS — 프론트(5173)·콘솔(5174) 배포 도메인을 콤마로 추가
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    # --- DB: 로컬 SQLite / 배포 MariaDB ---
    # 【수동·.env】 로컬 기본 sqlite / Docker·배포는 mariadb
    # 조건: DB_DIALECT=mariadb 이면 MARIADB_* 계정·DB 가 실제로 존재해야 함
    # 기능: users · auth_* · jobs · batch_jobs (서비스 DB). 피드백·학습 데이터는 아래 학습 DB
    db_dialect: str = Field(default="sqlite", alias="DB_DIALECT")
    # 전체 URL 덮어쓰기 (있으면 dialect 헬퍼보다 우선)
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    sqlite_path: str = Field(default="data/cutnkeep.db", alias="SQLITE_PATH")
    mariadb_host: str = Field(default="localhost", alias="MARIADB_HOST")
    mariadb_port: int = Field(default=3306, alias="MARIADB_PORT")
    mariadb_user: str = Field(default="cutnkeep", alias="MARIADB_USER")
    # 【보안】 배포 시 기본 비밀번호 교체 필수
    mariadb_password: str = Field(default="cutnkeep", alias="MARIADB_PASSWORD")
    mariadb_database: str = Field(default="cutnkeep", alias="MARIADB_DATABASE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # --- 학습 데이터 DB (서비스 DB 와 분리) ---
    # 서비스 DB(위 DB_*): users · auth_* · jobs · batch_jobs — 로컬 SQLite
    # 학습 DB: feedbacks(사용자·실패 피드백 이벤트) · learning_samples(학습 데이터 카탈로그: 경로·라벨·출처·split·검수)
    #   이미지·영상 자체는 DB 에 넣지 않고 data/feedback · data/pseudo_labels 파일 경로만 기록
    # 【수동·.env】 기본 mariadb (MARIADB_* 계정 재사용). 접속 실패 시 LEARNING_DB_FALLBACK_SQLITE 면 로컬 파일로
    learning_db_dialect: str = Field(default="mariadb", alias="LEARNING_DB_DIALECT")
    learning_database_url_override: str | None = Field(default=None, alias="LEARNING_DATABASE_URL")
    learning_sqlite_path: str = Field(default="data/learning.db", alias="LEARNING_SQLITE_PATH")
    learning_db_fallback_sqlite: bool = Field(default=True, alias="LEARNING_DB_FALLBACK_SQLITE")
    learning_db_connect_timeout: int = Field(default=3, alias="LEARNING_DB_CONNECT_TIMEOUT")
    # 기동 시 data/feedback · data/pseudo_labels 사이드카 중 DB 에 없는 것을 적재 (멱등)
    learning_sync_on_start: bool = Field(default=True, alias="LEARNING_SYNC_ON_START")
    # 로그인 회원의 요청 문장 + 시스템 해석을 검수 후보(source=request)로 기록 → 승인되면 LoRA·RAG 학습 데이터
    # (비로그인 요청은 저장하지 않으므로 대상 아님)
    learning_collect_requests: bool = Field(default=True, alias="LEARNING_COLLECT_REQUESTS")
    # 승인된 사용자 문장이 이만큼 새로 쌓이면 LoRA 재학습 (scripts/retrain_lora.py 기본값 · 콘솔 진행 표시)
    lora_retrain_min_new: int = Field(default=200, alias="LORA_RETRAIN_MIN_NEW")


    # --- 세그/검증 임계값 (Phase 1 기본) ---
    # 【수동·튜닝】 env 미노출 필드 — 코드에서 숫자 직접 조정 가능
    # 조건/기능:
    #   mask_*_area_ratio → 마스크가 너무 작/크면 fallback (재시도·피드백)
    #   min_confidence    → YOLO conf 평균 미달 시 fallback, 클래스 필터에도 사용
    #   max_image_side    → 전처리 리사이즈 긴 변 (속도·VRAM)
    #   clahe_*           → 대비 향상 강도 (세그 경계 품질에 영향)
    mask_min_area_ratio: float = 0.005  # 이보다 작으면 fallback
    mask_max_area_ratio: float = 0.95  # 이보다 크면 fallback
    min_confidence: float = 0.25
    max_image_side: int = 1280  # 전처리 긴 변 상한
    clahe_clip_limit: float = 2.0
    clahe_tile_size: int = 8

    @property
    def console_admin_set(self) -> set[str]:
        """CONSOLE_ADMINS → 소문자 아이디 집합 (아이디는 소문자로 저장된다)."""
        return {name.strip().lower() for name in self.console_admins.split(",") if name.strip()}

    @property
    def allowed_mime_list(self) -> List[str]:
        """쉼표 구분 MIME 문자열 → 리스트."""
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        """쉼표 구분 CORS origin → 리스트."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        """업로드 상한 바이트."""
        return self.max_upload_size_mb * 1024 * 1024

    @staticmethod
    def _resolve(relative: str, root: Path) -> Path:
        path = Path(relative)
        if path.is_absolute():
            return path
        return (root / path).resolve()

    def resolve_runtime_path(self, relative: str) -> Path:
        """서비스 런타임 경로: 상대 경로면 backend/ 기준 절대 경로."""
        return self._resolve(relative, _backend_root())

    def resolve_shared_path(self, relative: str) -> Path:
        """학습 공유 경로: 상대 경로면 저장소 루트 기준 절대 경로."""
        return self._resolve(relative, _project_root())

    # --- 서비스 런타임 (backend/) ---
    @property
    def upload_path(self) -> Path:
        return self.resolve_runtime_path(self.upload_dir)

    @property
    def log_path(self) -> Path:
        return self.resolve_runtime_path(self.log_dir)

    @property
    def yolo_model_file(self) -> Path:
        return self.resolve_runtime_path(self.yolo_model_path)

    @property
    def stuff_model_file(self) -> Path:
        return self.resolve_runtime_path(self.stuff_model_path)

    # --- 학습 공유 (저장소 루트) ---
    @property
    def feedback_path(self) -> Path:
        return self.resolve_shared_path(self.feedback_dir)

    @property
    def pseudo_label_path(self) -> Path:
        return self.resolve_shared_path(self.pseudo_label_dir)

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy URL 해석.
        - DATABASE_URL 환경변수가 있으면 최우선
        - 아니면 sqlite → backend/ 하위 파일 (서비스 런타임, 로컬 기본)
        - 아니면 mariadb → mysql+pymysql://...
        """
        if self.database_url_override:
            return self.database_url_override

        dialect = (self.db_dialect or "sqlite").strip().lower()
        if dialect in {"sqlite", "local"}:
            path = self.resolve_runtime_path(self.sqlite_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path.as_posix()}"

        if dialect in {"mariadb", "mysql"}:
            user = self.mariadb_user
            password = self.mariadb_password
            host = self.mariadb_host
            port = self.mariadb_port
            db = self.mariadb_database
            return (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
                f"?charset=utf8mb4"
            )

        raise ValueError(
            f"지원하지 않는 DB_DIALECT={self.db_dialect!r}. 'sqlite' 또는 'mariadb'를 사용하세요."
        )

    def _mariadb_url(self, connect_timeout: int | None = None) -> str:
        url = (
            f"mysql+pymysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_database}?charset=utf8mb4"
        )
        return f"{url}&connect_timeout={connect_timeout}" if connect_timeout else url

    @property
    def learning_sqlite_url(self) -> str:
        """학습 DB 의 로컬 SQLite (dialect=sqlite 또는 MariaDB 접속 실패 fallback)."""
        path = self.resolve_runtime_path(self.learning_sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"

    @property
    def learning_database_url(self) -> str:
        """학습 DB URL. LEARNING_DATABASE_URL > LEARNING_DB_DIALECT(mariadb|sqlite)."""
        if self.learning_database_url_override:
            return self.learning_database_url_override
        dialect = (self.learning_db_dialect or "mariadb").strip().lower()
        if dialect in {"sqlite", "local"}:
            return self.learning_sqlite_url
        if dialect in {"mariadb", "mysql"}:
            return self._mariadb_url(self.learning_db_connect_timeout)
        raise ValueError(
            f"지원하지 않는 LEARNING_DB_DIALECT={self.learning_db_dialect!r}. 'mariadb' 또는 'sqlite'를 사용하세요."
        )


@lru_cache
def get_settings() -> Settings:
    """캐시된 Settings 싱글톤 (프로세스당 1회 로드)."""
    return Settings()


