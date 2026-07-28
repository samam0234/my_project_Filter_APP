"""사용자 피드백 라우터 — DB 저장 (+ 선택적 파일 사이드카).

엔드포인트:
  POST /api/v1/feedback  — like/dislike + 선택 코멘트
"""

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
    """프론트 좋아요/싫어요 버튼에서 호출.

    FeedbackService 가 DB + data/feedback 사이드카에 기록한다.
    dislike 일 때 메시지를 조금 다르게 돌려 UX 를 구분한다.
    """
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
            "감사합니다 — 실패 케이스를 저장했습니다."
            if body.vote == FeedbackVote.DISLIKE
            else "피드백 감사합니다."
        ),
    )
