"""User feedback router — persists to DB (+ optional file sidecar)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import FeedbackVote
from app.db.session import get_db
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    service = FeedbackService(db=db)
    row, path = service.save_case(
        job_id=body.job_id,
        vote=body.vote,
        meta={"source": "user"},
        comment=body.comment,
    )
    return FeedbackResponse(
        ok=True,
        job_id=body.job_id,
        feedback_id=row.id if row else None,
        saved_path=str(path) if path else None,
        message=(
            "Thanks — failure case stored."
            if body.vote == FeedbackVote.DISLIKE
            else "Thanks for the feedback."
        ),
    )
