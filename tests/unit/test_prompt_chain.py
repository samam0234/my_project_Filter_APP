# -*- coding: utf-8 -*-
"""프롬프트 해석 체인(LangChain Core) — 키워드 파서와 같으면 1번, 다르면 다수결."""

from __future__ import annotations

import pytest

pytest.importorskip("langchain_core")

from app.core.config import Settings
from app.schemas.request import ParsedPrompt
from app.services import prompt_chain
from app.services.prompt_spec import LLMError


def _settings(**v) -> Settings:
    return Settings.model_validate({"DB_DIALECT": "sqlite", "PROMPT_CHAIN": "langchain", "PROMPT_VOTES": 3, **v})


def _p(*targets, effect="remove_bg") -> ParsedPrompt:
    return ParsedPrompt(target=list(targets), effect=effect)


@pytest.fixture()
def llm(monkeypatch):
    """LLM 답을 차례로 돌려주는 가짜. calls 로 호출 수를 센다."""
    class Fake:
        def __init__(self):
            self.answers, self.calls = [], 0

        def __call__(self, prompt, settings, examples=""):
            self.calls += 1
            item = self.answers[min(self.calls - 1, len(self.answers) - 1)]
            if isinstance(item, Exception):
                raise item
            return item

    fake = Fake()
    monkeypatch.setattr(prompt_chain, "parse_prompt_llm", fake)
    monkeypatch.setattr(prompt_chain, "_CHAIN", None)
    return fake


def test_fast_path_one_call_when_llm_agrees_with_keyword_parser(llm):
    llm.answers = [_p("dog")]
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings())
    assert out.target == ["dog"] and llm.calls == 1  # 평소 지연이 늘지 않는다


def test_disagreement_asks_again_and_majority_wins(llm):
    # 키워드 파서 = [dog]. 첫 답이 [dog, person](방해물까지 대상) → 더 묻고 [dog] 두 번 → 다수결로 [dog]
    llm.answers = [_p("dog", "person"), _p("dog"), _p("dog")]
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings())
    assert out.target == ["dog"] and llm.calls == 3


def test_keyword_parser_breaks_a_split_vote(llm):
    # 3번이 모두 다르면 키워드 파서의 표가 결정한다 (LLM 표는 각 1)
    llm.answers = [_p("cat"), _p("dog", "person"), _p("dog")]
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings())
    assert out.target == ["dog"]


def test_winner_keeps_effect_and_selector_of_its_own_answer(llm):
    llm.answers = [_p("dog", "person", effect="blur"), _p("dog", effect="crop"), _p("dog", effect="crop")]
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings())
    assert out.target == ["dog"] and out.effect == "crop"


def test_extra_call_failures_are_ignored_but_first_failure_propagates(llm):
    llm.answers = [_p("dog", "person"), LLMError("timeout"), LLMError("timeout")]
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings())
    assert out.target == ["dog", "person"] and llm.calls == 2  # 추가 호출이 한 번 실패하면 멈추고, 있는 답(1개)을 그대로 — 투표할 것이 없다
    llm.calls, llm.answers = 0, [LLMError("down")]
    with pytest.raises(LLMError):
        prompt_chain.parse_prompt_chain("강아지만", _settings())  # 첫 호출 실패는 올려서 호출 측이 폴백하게


def test_legacy_mode_and_single_vote_skip_the_chain(llm):
    llm.answers = [_p("dog", "person")]
    assert prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings(PROMPT_CHAIN="legacy")).target == ["dog", "person"]
    assert prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", _settings(PROMPT_VOTES=1)).target == ["dog", "person"]
    assert llm.calls == 2


def test_provider_off_means_no_llm(llm):
    llm.answers = [None]
    with pytest.raises(LLMError):
        prompt_chain.parse_prompt_chain("강아지만", _settings())


def test_node_passes_its_own_llm_function_so_tests_never_reach_ollama(monkeypatch):
    """prompt_analyzer 가 체인을 쓸 때도 nodes.parse_prompt_llm 을 교체하면 그 가짜가 쓰인다 (실제 Ollama 호출 방지)."""
    from app.core.config import get_settings
    from app.workflows import nodes

    calls = []
    monkeypatch.setattr(nodes, "parse_prompt_llm", lambda prompt, settings, **kw: calls.append(prompt) or _p("dog"))
    monkeypatch.setattr(prompt_chain, "parse_prompt_llm", lambda *a, **k: (_ for _ in ()).throw(AssertionError("실제 LLM 호출")))
    monkeypatch.setattr(get_settings(), "prompt_chain", "langchain")
    out = nodes.prompt_analyzer({"prompt": "강아지만 남기고 사람은 지워줘", "job_id": "zz-chain-node"})
    assert out["parsed_prompt"]["target"] == ["dog"] and calls == ["강아지만 남기고 사람은 지워줘"]


def test_second_opinion_uses_other_provider_only_when_split(monkeypatch):
    """LoRA 먼저 → 키워드 파서와 갈릴 때만 Ollama 한 번 → LoRA · Ollama · 키워드 파서 셋이 투표."""
    seen = []

    def ask(prompt, settings, examples=""):
        seen.append(settings.llm_provider)
        return _p("dog", "person") if settings.llm_provider == "lora" else _p("dog")

    monkeypatch.setattr(prompt_chain, "parse_prompt_llm", ask)
    monkeypatch.setattr(prompt_chain, "_CHAIN", None)
    s = _settings(LLM_PROVIDER="lora", PROMPT_SECOND_OPINION="ollama", PROMPT_VOTES=2)
    out = prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", s)
    assert seen == ["lora", "ollama"] and out.target == ["dog"]  # Ollama + 키워드 파서 2표 > LoRA 1표

    seen.clear()
    monkeypatch.setattr(prompt_chain, "parse_prompt_llm", lambda p, st, e="": seen.append(st.llm_provider) or _p("dog"))
    prompt_chain.parse_prompt_chain("강아지만 남기고 사람은 지워줘", s)
    assert seen == ["lora"]  # 키워드 파서와 같으면 Ollama 는 부르지 않는다
