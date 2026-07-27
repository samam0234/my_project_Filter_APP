"""User feedback endpoint (like / dislike)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.constants import FeedbackVote
from app.models.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    service = FeedbackService()
    path = service.save_case(
        job_id=body.job_id,
        vote=body.vote,
        meta={"source": "user"},
        comment=body.comment,
    )
    # dislike already saved; like also recorded for training signal balance
    return FeedbackResponse(
        ok=True,
        job_id=body.job_id,
        saved_path=str(path),
        message=(
            "Thanks — failure case stored."
            if body.vote == FeedbackVote.DISLIKE
            else "Thanks for the feedback."
        ),
    )
