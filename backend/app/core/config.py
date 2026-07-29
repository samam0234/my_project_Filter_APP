"""중앙 설정 (Pydantic Settings). 경로·모델명은 여기서만 관리.

환경변수 / .env 로 덮어쓴다 (alias = 환경변수 이름).
경로 프로퍼티(upload_path 등)는 항상 프로젝트 루트 기준 절대 경로로 해석.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """
    data/models 루트 경로 해석.
    - 로컬 모노레포: 저장소 루트 (…/CutNKeep)
    - Docker (backend 전용 이미지): 작업 디렉터리 (/app)
    """
    here = Path(__file__).resolve()
    backend_root = here.parents[2]  # …/backend or /app
    repo_candidate = here.parents[3]
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

    # --- 모델·데이터 경로 (상대 경로는 프로젝트 루트 기준) ---
    # 【수동·필수】 YOLO_MODEL_PATH
    # 조건:
    #   1) 파일을 저장소 루트 기준 경로에 직접 배치 (git 에 안 올라감)
    #   2) 서비스 본선은 **세그** 가중치 (yolo26s-seg.pt 또는 .onnx)
    #   3) 없으면 segmentation 이 stub 타원 마스크로 동작 (데모용)
    # 기능: Segmentor 가 Ultralytics/ONNX 로 로드하는 유일한 경로 설정
    # 학습 후: training/outputs/.../best.pt → models/ 로 복사 후 이 값 갱신
    yolo_model_path: str = Field(
        default="models/yolo26s-seg.pt",
        alias="YOLO_MODEL_PATH",
    )
    # 【수동】 디스크 경로 — 용량·백업 정책에 맞게 변경 가능
    upload_dir: str = Field(default="data/uploads", alias="UPLOAD_DIR")
    feedback_dir: str = Field(default="data/feedback", alias="FEEDBACK_DIR")
    pseudo_label_dir: str = Field(
        default="data/pseudo_labels",
        alias="PSEUDO_LABEL_DIR",
    )

    # --- LLM: ollama(기본) | openai | gemini | heuristic ---
    # 참고: docs/plan/AI_MODEL_STRATEGY.md
    # 필드 정의는 완료. 실제 호출 코드는 nodes.py
    # 「하드코딩 파트 부분 : [LLM 프롬프트 분석 연결]」 에서 작성.

    # ---
    # 제목 (하드코딩 파트 부분 : [LLM Settings 사용 — 코드는 nodes.py])
    # [관련 작업 임무 및 역할]
    #   아래 환경변수를 prompt_analyzer 에서 읽어 LLM 을 호출하게 연결한다.
    #   (이 파일에서는 값을 추가·기본값 조정만; HTTP 호출 본문은 nodes.py)
    # [기능하고 연결된 변수 및 함수]
    #   llm_provider, llm_base_url, ollama_model,
    #   openai_api_key, openai_model, gemini_api_key, gemini_model
    #   → workflows/nodes.py prompt_analyzer
    # [작성해야 하는 방식 및 규칙]
    #   1) .env 와 alias 이름 일치 유지.
    #   2) 새 provider 추가 시 Field 한 줄 + nodes 분기 동시.
    #   3) 시크릿(API 키) 기본값은 빈 문자열, 커밋 금지.
    # [코드 방식 힌트]
    #   # nodes 에서: settings = get_settings(); settings.llm_provider ...
    # ---
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

    def resolve_path(self, relative: str) -> Path:
        """상대 경로면 프로젝트 루트 기준 절대 경로."""
        path = Path(relative)
        if path.is_absolute():
            return path
        root = _project_root()
        return (root / path).resolve()

    @property
    def upload_path(self) -> Path:
        return self.resolve_path(self.upload_dir)

    @property
    def feedback_path(self) -> Path:
        return self.resolve_path(self.feedback_dir)

    @property
    def pseudo_label_path(self) -> Path:
        return self.resolve_path(self.pseudo_label_dir)

    @property
    def yolo_model_file(self) -> Path:
        return self.resolve_path(self.yolo_model_path)

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy URL 해석.
        - DATABASE_URL 환경변수가 있으면 최우선
        - 아니면 sqlite → 프로젝트 루트 하위 파일 (로컬 기본)
        - 아니면 mariadb → mysql+pymysql://...
        """
        if self.database_url_override:
            return self.database_url_override

        dialect = (self.db_dialect or "sqlite").strip().lower()
        if dialect in {"sqlite", "local"}:
            path = self.resolve_path(self.sqlite_path)
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


