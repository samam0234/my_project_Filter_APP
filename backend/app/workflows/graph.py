"""컷앤킵 LangGraph 파이프라인 컴파일 및 실행.

이 모듈은 전체 처리 그래프의 **조립·실행 진입점**이다.

흐름 요약:
  prompt_analyzer → preprocessor → segmentor → validator
       ├─ ok              → effect_applier → END
       ├─ fallback(재시도) → increment_retry → segmentor
       └─ failed/소진      → feedback_collector → effect_applier → END

langgraph 패키지가 없으면 _run_linear 로 동일한 경로를 순차 실행한다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from app.core.constants import JobStatus
from app.schemas.request import ParsedPrompt
from app.schemas.response import ProcessResult
from app.workflows import edges, nodes
from app.workflows.state import GraphState


def build_graph():
    """
    langgraph 설치 시 StateGraph 구성.
    import 실패 시 선형 runner로 fallback (개발 스캐폴드).

    반환:
      - 컴파일된 그래프 (invoke 가능)
      - 또는 None → 호출측에서 _run_linear 사용
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        logger.warning("langgraph 미설치 — 선형 fallback runner 사용")
        return None

    # GraphState 를 공유 상태로 쓰는 StateGraph
    graph = StateGraph(GraphState)

    # --- 노드 등록 (실제 로직은 nodes / edges 모듈) ---
    graph.add_node("prompt_analyzer", nodes.prompt_analyzer)
    graph.add_node("preprocessor", nodes.preprocessor)
    graph.add_node("segmentor", nodes.segmentor)
    graph.add_node("validator", nodes.validator_node)
    graph.add_node("effect_applier", nodes.effect_applier)
    graph.add_node("feedback_collector", nodes.feedback_collector)
    # 재시도 카운트만 올리는 경량 노드
    graph.add_node("increment_retry", edges.increment_retry)

    # --- 고정 엣지: 분석 → 전처리 → 세그 → 검증 ---
    graph.set_entry_point("prompt_analyzer")
    graph.add_edge("prompt_analyzer", "preprocessor")
    graph.add_edge("preprocessor", "segmentor")
    graph.add_edge("segmentor", "validator")

    # --- 조건부 분기: validator 결과에 따라 다음 노드 결정 ---
    graph.add_conditional_edges(
        "validator",
        edges.after_validator,  # 라우팅 함수 → 문자열 키 반환
        {
            "effect_applier": "effect_applier",
            "retry_segmentor": "increment_retry",
            "feedback_then_effects": "feedback_collector",
        },
    )
    # 재시도: 카운트 증가 후 다시 세그
    graph.add_edge("increment_retry", "segmentor")
    # 실패/소진 후에도 UX 를 위해 효과는 best-effort 적용
    graph.add_edge("feedback_collector", "effect_applier")
    graph.add_edge("effect_applier", END)

    return graph.compile()


# 프로세스 전역 컴파일 캐시 (첫 요청 시 1회 빌드)
_COMPILED = None


def get_compiled_graph():
    """컴파일된 그래프 싱글톤. 없거나 빌드 실패 시 None."""
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_graph()
    return _COMPILED


def _run_linear(state: GraphState) -> GraphState:
    """langgraph 없이 Phase 1 선형 경로 (항상 사용 가능).

    그래프의 조건부 분기 로직을 순차 if 로 재현한다.
    개발·CI·langgraph 미설치 환경에서 e2e 를 보장하기 위함.
    """
    state = nodes.prompt_analyzer(state)
    state = nodes.preprocessor(state)
    # 전처리 단계에서 이미 실패하면 피드백만 남기고 종료
    if state.get("status") == JobStatus.FAILED.value:
        state = nodes.feedback_collector(state)
        return state
    state = nodes.segmentor(state)
    state = nodes.validator_node(state)
    route = edges.after_validator(state)
    # 1회 재시도: 카운트 올린 뒤 세그·검증 한 번 더
    if route == "retry_segmentor":
        state = edges.increment_retry(state)
        state = nodes.segmentor(state)
        state = nodes.validator_node(state)
        route = edges.after_validator(state)
    if route == "feedback_then_effects":
        state = nodes.feedback_collector(state)
    state = nodes.effect_applier(state)
    return state


def run_pipeline(
    image_bytes: bytes,
    prompt: str,
    job_id: Optional[str] = None,
) -> ProcessResult:
    """공개 진입점: 이미지 + 프롬프트 → ProcessResult.

    라우터(upload 등)가 호출하는 유일한 고수준 API.
    job_id 가 없으면 uuid4 hex 를 발급한다.
    """
    job_id = job_id or uuid4().hex
    # GraphState 초기값 — 노드들이 점진적으로 필드를 채움
    initial: GraphState = {
        "job_id": job_id,
        "image_bytes": image_bytes,
        "prompt": prompt,
        "status": JobStatus.PENDING.value,
        "retry_count": 0,
        "feedback_saved": False,
        "quality_score": 0.0,
    }

    compiled = get_compiled_graph()
    try:
        if compiled is not None:
            # LangGraph invoke: 상태 dict 입출력
            final: Dict[str, Any] = compiled.invoke(initial)
        else:
            final = _run_linear(initial)
    except Exception as exc:
        # 예상 밖 예외도 실패 상태로 정규화 + 피드백 시도
        logger.exception("파이프라인 실패: {}", exc)
        final = {
            **initial,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "message": str(exc),
        }
        try:
            final = nodes.feedback_collector(final)  # type: ignore[arg-type]
        except Exception:
            pass
    finally:
        # 결과에서 대용량 바이트 제거, 디스크 경로만 유지
        # (인메모리 _IMAGE_CACHE 정리)
        nodes.clear_job_cache(job_id)

    # state 의 dict → Pydantic ParsedPrompt (응답 스키마용)
    parsed_raw = final.get("parsed_prompt") or {}
    parsed = ParsedPrompt(**parsed_raw) if parsed_raw else None

    return ProcessResult(
        job_id=job_id,
        status=str(final.get("status") or JobStatus.FAILED.value),
        quality_score=float(final.get("quality_score") or 0.0),
        message=final.get("error") or final.get("message"),
        parsed_prompt=parsed,
        before_path=final.get("before_path"),
        after_path=final.get("after_path"),
        feedback_saved=bool(final.get("feedback_saved")),
        meta={
            "backend": final.get("backend"),
            "labels": final.get("labels"),
            "confidences": final.get("confidences"),
        },
    )
