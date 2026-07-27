"""Conditional edges for LangGraph."""

from __future__ import annotations

from app.core.constants import JobStatus
from app.workflows.state import GraphState


def after_validator(state: GraphState) -> str:
    """
    Route after validator:
      - ok → effect_applier
      - fallback with retries left → segmentor (retry)
      - failed / exhausted → feedback_collector then still try effects for UX
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
