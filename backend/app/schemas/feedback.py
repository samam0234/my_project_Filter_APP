"""Feedback request/response schemas (Pydantic)."""

from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import FeedbackVote


class FeedbackRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    vote: FeedbackVote
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    ok: bool = True
    job_id: str
    feedback_id: Optional[str] = None
    saved_path: Optional[str] = None
    message: str = "Feedback recorded."
