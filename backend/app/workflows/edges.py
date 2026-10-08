"""LangGraph 조건부 엣지.

validator 노드 이후 **어디로 갈지** 결정하는 라우팅 함수만 모은다.
무거운 연산은 없고 state 필드 몇 개만 본다.
"""

from __future__ import annotations

from app.core.constants import JobStatus
from app.workflows.state import GraphState


def is_hard_example(state: GraphState) -> bool:
    """HARD_EXAMPLE_CONF 가 켜져 있고 고른 인스턴스의 최소 신뢰도가 그보다 낮은가."""
    from app.core.config import get_settings

    threshold = get_settings().hard_example_conf
    conf_min = (state.get("leak") or {}).get("conf_min")
    return threshold > 0 and conf_min is not None and conf_min < threshold


def after_validator(state: GraphState) -> str:
    """
    validator 이후 분기 키를 반환한다.

    반환 문자열은 graph.py 의 conditional_edges 맵 키와 일치해야 한다.

      - "effect_applier"        : 품질 OK → 바로 효과 적용
      - "retry_segmentor"       : fallback 이고 재시도 여유 있음 → 세그 재시도
      - "feedback_then_effects" : failed 또는 재시도 소진, 또는 어려운 사례(HARD_EXAMPLE_CONF) → 피드백 저장 후 효과

    정책 요약:
      ok          → 효과
      fallback + retry_count < 1 → 재시도
      그 외       → 피드백 + best-effort 효과 (UX 유지)
    """
    status = state.get("status") or JobStatus.FAILED.value
    retries = int(state.get("retry_count") or 0)

    # =============================================================================
    # [이미 구현된 구간 · 바이브] validator 이후 라우팅
    # -----------------------------------------------------------------------------
    # 하드코딩 숙제 아님. 재시도 횟수(N)만 정책 튜닝 시 숫자 변경.
    # =============================================================================
    if status == JobStatus.OK.value:
        # 어려운 사례(처리는 됐지만 확신이 낮은 선택)는 학습 후보로도 남긴다 — 비로그인(persist=False)은 저장하지 않는다
        if state.get("persist") is not False and is_hard_example(state):
            return "feedback_then_effects"
        return "effect_applier"

    if status == JobStatus.FALLBACK.value and retries < 1:
        return "retry_segmentor"

    return "feedback_then_effects"


def increment_retry(state: GraphState) -> GraphState:
    """재시도 카운트를 1 증가시킨 상태 반환.

    graph 에서는 이 노드 다음에 다시 segmentor 로 이어진다.
    """
    return {**state, "retry_count": int(state.get("retry_count") or 0) + 1}
