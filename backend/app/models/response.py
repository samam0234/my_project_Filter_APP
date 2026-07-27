"""API response schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.request import ParsedPrompt


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    phase: int = 1


class ProcessResult(BaseModel):
    """Internal processing outcome (mapped to UploadResponse)."""

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
