"""프롬프트 해석 체인 — LangChain Core Runnable 로 조립한 "묻고 → 검증하고 → 필요하면 다수결".

왜: LLM 은 같은 문장에도 물을 때마다 다른 대상을 내는 경우가 있다 (평가: 같은 143문장을 세 번 물었을 때 대상 정확도가
라운드마다 달랐고, "X 말고 Y만"에서 X 까지 대상으로 내는 "초과"가 간헐적으로 나왔다). 대상이 틀리면 뒤 단계가 아무리
좋아도 지정하지 않은 것이 남으므로 해석 단계에서 안정화한다.

흐름 (LCEL)
  _init  →  _sample(LLM 1회)  →  [휴리스틱과 대상이 같다?  예: 그대로 확정 / 아니오: _resample(최대 N회 더)]  →  _decide
  _decide: LLM 답들의 대상 집합에 투표 + 키워드 파서(heuristic_targets)가 한 표. 이긴 대상 집합을 낸 첫 LLM 답을 채택
           (효과·선택자 등은 그 답을 그대로 쓴다). 동률이면 LLM 답이 많은 쪽, 그래도 같으면 먼저 나온 것.
  빠른 길: 첫 답이 키워드 파서와 같으면 호출은 1번 — 평소 지연이 늘지 않는다.

LLM 호출 자체(provider·fallback·RAG 예시 붙이기)는 기존 prompt_llm.parse_prompt_llm 을 그대로 쓴다.
PROMPT_CHAIN=legacy 면 이 체인을 건너뛴다.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from loguru import logger

from app.core.config import Settings, get_settings
from app.schemas.request import ParsedPrompt
from app.services.heuristic_targets import detect_targets
from app.services.prompt_llm import parse_prompt_llm
from app.services.prompt_spec import LLMError


class ChainState(TypedDict, total=False):
    prompt: str
    settings: Settings
    examples: str
    samples: List[ParsedPrompt]
    heuristic: List[str]
    parsed: ParsedPrompt
    info: Dict[str, Any]


def _targets(parsed: ParsedPrompt) -> tuple:
    return tuple(sorted(parsed.target))


def _init(state: ChainState) -> ChainState:
    return {**state, "samples": [], "heuristic": detect_targets(state["prompt"].lower()), "info": {}}


def _sample(state: ChainState) -> ChainState:
    """LLM 한 번. 첫 호출의 실패는 그대로 올려 호출 측이 키워드 파서로 내려가게 한다 (예전 동작)."""
    parsed = parse_prompt_llm(state["prompt"], state["settings"], state.get("examples", ""))
    if parsed is None:  # provider 가 LLM 이 아님 (체인을 쓸 이유가 없다)
        raise LLMError("LLM provider 가 꺼져 있음")
    return {**state, "samples": [*state["samples"], parsed]}


def _agrees(state: ChainState) -> bool:
    return _targets(state["samples"][0]) == tuple(sorted(state["heuristic"]))


def _needs_more(state: ChainState) -> bool:
    return len(state["samples"]) < state["settings"].prompt_votes and not _agrees(state)


def _resample(state: ChainState) -> ChainState:
    """키워드 파서와 의견이 갈릴 때만 — 총 PROMPT_VOTES 개가 될 때까지 더 묻는다 (추가 호출의 실패는 무시)."""
    samples = list(state["samples"])
    while len(samples) < state["settings"].prompt_votes:
        try:
            more = parse_prompt_llm(state["prompt"], state["settings"], state.get("examples", ""))
        except LLMError as exc:
            logger.warning("추가 LLM 호출 실패 — 있는 답으로 다수결: {}", exc)
            break
        if more is not None:
            samples.append(more)
    return {**state, "samples": samples}


def _decide(state: ChainState) -> ChainState:
    samples, heuristic = state["samples"], tuple(sorted(state["heuristic"]))
    votes: Counter = Counter(_targets(p) for p in samples)
    llm_votes = dict(votes)
    if len(samples) > 1:  # 한 번만 물었다면(= 키워드 파서와 같았거나 추가 호출이 모두 실패) 투표할 것이 없다
        votes[heuristic] += 1
    best = max(votes.values())
    tied = [t for t, c in votes.items() if c == best]
    # 동률: LLM 표가 많은 쪽 → 먼저 나온 것
    winner = max(tied, key=lambda t: (llm_votes.get(t, 0), -next((i for i, p in enumerate(samples) if _targets(p) == t), 99)))
    parsed = next((p for p in samples if _targets(p) == winner), None)
    decided_by = "llm"
    if parsed is None:  # 키워드 파서만 이긴 경우 — 가장 가까운 LLM 답의 효과·선택자를 가져와 대상만 바꾼다
        parsed = samples[0].model_copy(update={"target": list(heuristic)})
        decided_by = "heuristic"
    elif len(samples) > 1:
        decided_by = "vote"
    info = {"samples": len(samples), "agreed_with_heuristic": _agrees(state), "decided_by": decided_by,
            "llm_votes": {"+".join(k): v for k, v in llm_votes.items()}}
    if decided_by != "llm":
        logger.info("해석 체인: {} → {} ({})", [list(_targets(p)) for p in samples], list(winner), decided_by)
    return {**state, "parsed": parsed, "info": info}


def build_prompt_chain():
    """LCEL 체인 — 입력 {prompt, settings, examples}, 출력 ChainState(parsed, info)."""
    return (
        RunnableLambda(_init)
        | RunnableLambda(_sample)
        | RunnableBranch((_needs_more, RunnableLambda(_resample)), RunnablePassthrough())
        | RunnableLambda(_decide)
    )


_CHAIN = None


def parse_prompt_chain(
    prompt: str,
    settings: Optional[Settings] = None,
    examples: str = "",
) -> Optional[ParsedPrompt]:
    """parse_prompt_llm 과 같은 계약 (ParsedPrompt | None, 실패는 LLMError) + 대상 안정화.

    PROMPT_CHAIN=legacy 이거나 PROMPT_VOTES<=1 이면 기존 단일 호출 그대로.
    """
    settings = settings or get_settings()
    if settings.prompt_chain != "langchain" or settings.prompt_votes <= 1:
        return parse_prompt_llm(prompt, settings, examples)
    global _CHAIN
    if _CHAIN is None:
        _CHAIN = build_prompt_chain()
    out = _CHAIN.invoke({"prompt": prompt, "settings": settings, "examples": examples})
    return out["parsed"]
