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

import time
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from loguru import logger

from app.core.constants import JobStatus
from app.schemas.request import ParsedPrompt
from app.schemas.response import ProcessResult
from app.workflows import edges, nodes
from app.workflows.state import GraphState


def _timed(name: str, fn: Callable[[GraphState], GraphState]) -> Callable[[GraphState], GraphState]:
    """노드 실행 시간을 state["timings"][name] 에 누적(ms)한다 — 어느 단계가 느린지 meta·로그로 확인."""

    def wrapper(state: GraphState) -> GraphState:
        started = time.perf_counter()
        out = fn(state)
        timings = dict(out.get("timings") or state.get("timings") or {})
        timings[name] = round(timings.get(name, 0.0) + (time.perf_counter() - started) * 1000, 1)
        return {**out, "timings": timings}

    wrapper.__name__ = getattr(fn, "__name__", name)
    return wrapper


# 그래프·선형 실행이 공유하는 노드 표 (이름 → 시간 측정 래핑 함수)
NODES: Dict[str, Callable[[GraphState], GraphState]] = {
    "prompt_analyzer": _timed("prompt_analyzer", nodes.prompt_analyzer),
    "preprocessor": _timed("preprocessor", nodes.preprocessor),
    "segmentor": _timed("segmentor", nodes.segmentor),
    "validator": _timed("validator", nodes.validator_node),
    "effect_applier": _timed("effect_applier", nodes.effect_applier),
    "feedback_collector": _timed("feedback_collector", nodes.feedback_collector),
}


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
    for name, fn in NODES.items():
        graph.add_node(name, fn)
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
    state = NODES["prompt_analyzer"](state)
    state = NODES["preprocessor"](state)
    # 전처리 단계에서 이미 실패하면 피드백만 남기고 종료
    if state.get("status") == JobStatus.FAILED.value:
        state = NODES["feedback_collector"](state)
        return state
    state = NODES["segmentor"](state)
    state = NODES["validator"](state)
    route = edges.after_validator(state)
    # 1회 재시도: 카운트 올린 뒤 조건을 바꿔 세그·검증 한 번 더
    if route == "retry_segmentor":
        state = edges.increment_retry(state)
        state = NODES["segmentor"](state)
        state = NODES["validator"](state)
        route = edges.after_validator(state)
    if route == "feedback_then_effects":
        state = NODES["feedback_collector"](state)
    state = NODES["effect_applier"](state)
    return state


def run_pipeline(
    image_bytes: bytes,
    prompt: str,
    job_id: Optional[str] = None,
    persist: bool = True,
    parsed: Optional[ParsedPrompt] = None,
) -> ProcessResult:
    """공개 진입점: 이미지 + 프롬프트 → ProcessResult.

    라우터(upload 등)가 호출하는 유일한 고수준 API.
    job_id 가 없으면 uuid4 hex 를 발급한다.
    persist=False (비로그인): 실패 케이스를 피드백(학습 재료)으로 저장하지 않는다.
    parsed: 이미 해석된 프롬프트 (배치가 같은 문장을 한 번만 해석해 넘김). 주면 LLM 해석을 건너뛴다.
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
        "persist": persist,
    }
    if parsed is not None:
        initial["parsed_prompt"] = parsed.model_dump()

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

    logger.info(
        "pipeline job={} status={} attempts={} timings(ms)={}",
        job_id,
        final.get("status"),
        final.get("attempts"),
        final.get("timings"),
    )

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
            "prompt_parser": final.get("prompt_parser"),
            "prompt_rag": final.get("prompt_rag"),
            "detected": final.get("detected"),
            "segment_strategy": final.get("segment_strategy"),
            "attempts": final.get("attempts"),
            "chosen_attempt": final.get("chosen_attempt"),
            "timings": final.get("timings"),
            "selection": final.get("selection"),
            "leak": final.get("leak"),
        },
    )
