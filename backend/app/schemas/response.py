"""API response schemas (Pydantic)."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.request import ParsedPrompt


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    phase: int = 1
    db_dialect: Optional[str] = None


class ProcessResult(BaseModel):
    """Internal processing outcome (mapped to UploadResponse / Job row)."""

    job_id: str
    status: str
    quality_score: float = 0.0
    message: Optional[str] = None
    parsed_prompt: Optional[ParsedPrompt] = None
    before_path: Optional[str] = None
    after_path: Optional[str] = None
    feedback_saved: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    job_id: str
    status: str
    parsed_prompt: Optional[ParsedPrompt] = None
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    quality_score: float = 0.0
    message: Optional[str] = None
    feedback_saved: bool = False


class JobResponse(BaseModel):
    """Persisted job view from DB."""

    job_id: str
    prompt: str
    status: str
    parsed_prompt: Optional[dict[str, Any]] = None
    quality_score: float = 0.0
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    backend: Optional[str] = None
    message: Optional[str] = None
    feedback_saved: bool = False
    created_at: Optional[str] = None
