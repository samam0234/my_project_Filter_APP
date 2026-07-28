"""LangGraph 조건부 엣지.

validator 노드 이후 **어디로 갈지** 결정하는 라우팅 함수만 모은다.
무거운 연산은 없고 state 필드 몇 개만 본다.
"""

from __future__ import annotations

from app.core.constants import JobStatus
from app.workflows.state import GraphState


def after_validator(state: GraphState) -> str:
    """
    validator 이후 분기 키를 반환한다.

    반환 문자열은 graph.py 의 conditional_edges 맵 키와 일치해야 한다.

      - "effect_applier"        : 품질 OK → 바로 효과 적용
      - "retry_segmentor"       : fallback 이고 재시도 여유 있음 → 세그 재시도
      - "feedback_then_effects" : failed 또는 재시도 소진 → 피드백 저장 후 효과

    정책 요약:
      ok          → 효과
      fallback + retry_count < 1 → 재시도
      그 외       → 피드백 + best-effort 효과 (UX 유지)
    """
    status = state.get("status") or JobStatus.FAILED.value
    retries = int(state.get("retry_count") or 0)

    if status == JobStatus.OK.value:
        return "effect_applier"

    # Phase 1: 재시도는 1회만 (retries < 1)
    if status == JobStatus.FALLBACK.value and retries < 1:
        return "retry_segmentor"

    # 재시도 소진 또는 하드 실패: 피드백 저장 후 best-effort 효과 적용
    return "feedback_then_effects"


def increment_retry(state: GraphState) -> GraphState:
    """재시도 카운트를 1 증가시킨 상태 반환.

    graph 에서는 이 노드 다음에 다시 segmentor 로 이어진다.
    """
    return {**state, "retry_count": int(state.get("retry_count") or 0) + 1}
