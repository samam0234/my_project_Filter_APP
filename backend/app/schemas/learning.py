"""운영 콘솔 학습 데이터 검수 API DTO."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LearningSampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    source: str
    status: str
    split: Optional[str] = None
    origin_id: str
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    prompt: Optional[str] = None
    answer: Optional[dict[str, Any]] = None
    has_image: bool = False
    image_url: Optional[str] = None
    note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class LearningSampleList(BaseModel):
    items: list[LearningSampleResponse]
    total: int
    limit: int
    offset: int


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "reset"]
    # 승인하면서 정답을 고칠 때 (ParsedPrompt JSON)
    answer: Optional[dict[str, Any]] = None
    note: Optional[str] = Field(default=None, max_length=1000)


class BulkReviewRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=500)
    action: Literal["approve", "reject"]


class BulkReviewResponse(BaseModel):
    done: int
    skipped: list[dict[str, str]]


class DeleteResponse(BaseModel):
    id: str
    removed_files: list[str]
