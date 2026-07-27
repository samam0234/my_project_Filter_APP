"""LangGraph 조건부 엣지."""

from __future__ import annotations

from app.core.constants import JobStatus
from app.workflows.state import GraphState


def after_validator(state: GraphState) -> str:
    """
    validator 이후 분기:
      - ok → effect_applier
      - fallback 이고 재시도 남음 → segmentor (재시도)
      - failed / 재시도 소진 → feedback_collector 후 효과 적용 (UX)
    """
    status = state.get("status") or JobStatus.FAILED.value
    retries = int(state.get("retry_count") or 0)

    if status == JobStatus.OK.value:
        return "effect_applier"

    if status == JobStatus.FALLBACK.value and retries < 1:
        return "retry_segmentor"

    # fallback exhausted or hard fail: collect feedback, then apply best-effort effects
    return "feedback_then_effects"


def increment_retry(state: GraphState) -> GraphState:
    return {**state, "retry_count": int(state.get("retry_count") or 0) + 1}
