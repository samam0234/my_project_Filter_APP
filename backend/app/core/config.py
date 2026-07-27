"""Centralized settings (Pydantic Settings). Paths and model names live here only."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """
    Resolve data/models root.
    - Local monorepo: repo root (…/CutNKeep)
    - Docker (backend-only image): backend workdir (/app)
    """
    here = Path(__file__).resolve()
    backend_root = here.parents[2]  # …/backend or /app
    repo_candidate = here.parents[3]
    if (repo_candidate / "frontend").is_dir() or (repo_candidate / "docs").is_dir():
        return repo_candidate
    return backend_root



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY")

    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    allowed_mime_types: str = Field(
        default="image/jpeg,image/png,image/webp",
        alias="ALLOWED_MIME_TYPES",
    )

    yolo_model_path: str = Field(
        default="models/yolov8n-seg.onnx",
        alias="YOLO_MODEL_PATH",
    )
    upload_dir: str = Field(default="data/uploads", alias="UPLOAD_DIR")
    feedback_dir: str = Field(default="data/feedback", alias="FEEDBACK_DIR")
    pseudo_label_dir: str = Field(
        default="data/pseudo_labels",
        alias="PSEUDO_LABEL_DIR",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    file_retention_hours: int = Field(default=24, alias="FILE_RETENTION_HOURS")

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    # Segmentation / validator thresholds (Phase 1 defaults)
    mask_min_area_ratio: float = 0.005
    mask_max_area_ratio: float = 0.95
    min_confidence: float = 0.25
    max_image_side: int = 1280
    clahe_clip_limit: float = 2.0
    clahe_tile_size: int = 8

    @property
    def allowed_mime_list(self) -> List[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def resolve_path(self, relative: str) -> Path:
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
