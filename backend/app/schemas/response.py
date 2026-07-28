"""API 응답 스키마 (Pydantic).

라우터 response_model 과 내부 ProcessResult 를 분리한다.
ProcessResult 는 파이프라인→레포지토리, UploadResponse 는 클라이언트 응답.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.request import ParsedPrompt


class HealthResponse(BaseModel):
    """GET /health 응답."""

    status: str = "ok"
    version: str = "0.1.0"
    phase: int = 1
    db_dialect: Optional[str] = None  # sqlite / mysql 등


class ProcessResult(BaseModel):
    """내부 처리 결과 (UploadResponse / Job 행에 매핑).

    run_pipeline 반환 타입. before_path/after_path 는 디스크 절대/상대 경로.
    """

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
    """POST /upload 클라이언트 응답.

    경로 대신 before_url / after_url (API 상대 경로) 를 준다.
    """

    job_id: str
    status: str
    parsed_prompt: Optional[ParsedPrompt] = None
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    quality_score: float = 0.0
    message: Optional[str] = None
    feedback_saved: bool = False


class JobResponse(BaseModel):
    """DB에 저장된 Job 조회 뷰."""

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
