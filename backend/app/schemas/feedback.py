"""피드백 요청/응답 스키마 (Pydantic).

POST /api/v1/feedback 의 body / response_model.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import FeedbackVote


class FeedbackRequest(BaseModel):
    """클라이언트가 보내는 평가 요청."""

    job_id: str = Field(..., min_length=1)  # 대상 처리 job
    vote: FeedbackVote  # like | dislike
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    """피드백 저장 결과."""

    ok: bool = True
    job_id: str
    feedback_id: Optional[str] = None  # DB PK (case_id)
    saved_path: Optional[str] = None  # JSON 사이드카 경로 (있을 때)
    message: str = "피드백이 기록되었습니다."
