"""Compile and run the Cut & Keep LangGraph pipeline."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from app.core.constants import JobStatus
from app.models.request import ParsedPrompt
from app.models.response import ProcessResult
from app.workflows import edges, nodes
from app.workflows.state import GraphState


def build_graph():
    """
    Build StateGraph when langgraph is installed.
    Falls back to a linear runner if import fails (dev scaffold).
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        logger.warning("langgraph not installed — using linear fallback runner")
        return None

    graph = StateGraph(GraphState)

    graph.add_node("prompt_analyzer", nodes.prompt_analyzer)
    graph.add_node("preprocessor", nodes.preprocessor)
    graph.add_node("segmentor", nodes.segmentor)
    graph.add_node("validator", nodes.validator_node)
    graph.add_node("effect_applier", nodes.effect_applier)
    graph.add_node("feedback_collector", nodes.feedback_collector)
    graph.add_node("increment_retry", edges.increment_retry)

    graph.set_entry_point("prompt_analyzer")
    graph.add_edge("prompt_analyzer", "preprocessor")
    graph.add_edge("preprocessor", "segmentor")
    graph.add_edge("segmentor", "validator")

    graph.add_conditional_edges(
        "validator",
        edges.after_validator,
        {
            "effect_applier": "effect_applier",
            "retry_segmentor": "increment_retry",
            "feedback_then_effects": "feedback_collector",
        },
    )
    graph.add_edge("increment_retry", "segmentor")
    graph.add_edge("feedback_collector", "effect_applier")
    graph.add_edge("effect_applier", END)

    return graph.compile()


_COMPILED = None


def get_compiled_graph():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_graph()
    return _COMPILED


def _run_linear(state: GraphState) -> GraphState:
    """Linear Phase-1 path without langgraph (always available)."""
    state = nodes.prompt_analyzer(state)
    state = nodes.preprocessor(state)
    if state.get("status") == JobStatus.FAILED.value:
        state = nodes.feedback_collector(state)
        return state
    state = nodes.segmentor(state)
    state = nodes.validator_node(state)
    route = edges.after_validator(state)
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
    """Public entry: image + prompt → ProcessResult."""
    job_id = job_id or uuid4().hex
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
            final: Dict[str, Any] = compiled.invoke(initial)
        else:
            final = _run_linear(initial)
    except Exception as exc:
        logger.exception("Pipeline failed: {}", exc)
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
        # drop heavy bytes from result; keep disk paths
        nodes.clear_job_cache(job_id)

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
