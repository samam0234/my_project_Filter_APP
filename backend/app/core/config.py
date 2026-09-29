"""중앙 설정 (Pydantic Settings). 경로·모델명은 여기서만 관리.

환경변수 / .env 로 덮어쓴다 (alias = 환경변수 이름).
경로는 두 기준으로 나눠 절대 경로로 해석한다.
  - 서비스 런타임 (backend/ 기준): uploads, SQLite DB, 앱 로그, 서빙 중인 모델
  - 학습 공유 자산 (저장소 루트 기준): feedback, pseudo_labels
Docker 에서는 둘 다 /app 이며, compose 마운트로 같은 역할 분리를 유지한다.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

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
    #   1) 서비스 본선은 **세그** 가중치 (yolo26s-seg.pt 또는 .onnx), git 에 안 올라감
    #   2) 없으면 segmentation 이 stub 타원 마스크로 동작 (데모용)
    # 기능: Segmentor 가 Ultralytics/ONNX 로 로드하는 유일한 경로 설정
    # 배포: 루트 models/(원본·후보 보관소) 또는 학습 best.pt
    #       → training/yolo/apply_best.py 가 backend/models/ 로 복사
    yolo_model_path: str = Field(
        default="models/yolo26s-seg.pt",
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
    # 【수동·선택】 LLM_PROVIDER=lora — training/lora 로 학습한 어댑터를 transformers 로 서빙
    # 경로는 backend/ 기준. 베이스는 HF 형식 폴더(config.json + safetensors), 어댑터는 서빙용 복사본
    lora_base_model: str = Field(default="", alias="LORA_BASE_MODEL")
    lora_adapter_path: str = Field(default="models/lora", alias="LORA_ADAPTER_PATH")

    # --- 계정 (로그인 · 회원가입 · 아이디/비밀번호 찾기) ---
    # 【수동·배포】 SESSION_COOKIE_SECURE — HTTPS 배포 시 true (로컬 http 는 false 여야 쿠키 저장)
    session_cookie_name: str = Field(default="cnk_session", alias="SESSION_COOKIE_NAME")
    session_ttl_hours: int = Field(default=168, alias="SESSION_TTL_HOURS")  # 7일
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
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
    file_retention_hours: int = Field(default=24, alias="FILE_RETENTION_HOURS")

    # 【수동】 CORS_ORIGINS — 프론트(5173)·콘솔(5174) 배포 도메인을 콤마로 추가
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    # --- DB: 로컬 SQLite / 배포 MariaDB ---
    # 【수동·.env】 로컬 기본 sqlite / Docker·배포는 mariadb
    # 조건: DB_DIALECT=mariadb 이면 MARIADB_* 계정·DB 가 실제로 존재해야 함
    # 기능: jobs/feedbacks/batch_jobs 테이블 영속화
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


@lru_cache
def get_settings() -> Settings:
    """캐시된 Settings 싱글톤 (프로세스당 1회 로드)."""
    return Settings()


