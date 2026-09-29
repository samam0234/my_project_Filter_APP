# -*- coding: utf-8 -*-
"""LLM 프롬프트 분석 테스트 (네트워크 없음).

_post_json 을 가짜로 바꿔 provider 별 요청 형식·응답 파싱·정규화,
그리고 prompt_analyzer 의 휴리스틱 fallback 을 확인한다.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic_settings")
pytest.importorskip("loguru")

from app.core.config import Settings
from app.services import prompt_llm
from app.services.prompt_llm import (
    LLMError,
    extract_json_object,
    normalize_parsed,
    parse_prompt_llm,
)


def _settings(**env) -> Settings:
    """alias(환경변수 이름)로 값을 넣은 Settings. 로컬 .env 보다 우선."""
    base = {"LLM_PROVIDER": "ollama", "OPENAI_API_KEY": "", "GEMINI_API_KEY": ""}
    return Settings(**{**base, **env})


# --- JSON 추출 · 정규화 ---


def test_extract_json_from_code_fence():
    text = '결과:\n```json\n{"target": ["dog"], "effect": "blur"}\n```'
    assert extract_json_object(text) == {"target": ["dog"], "effect": "blur"}


def test_extract_json_with_surrounding_noise():
    assert extract_json_object('Sure! {"target": "cat"} done')["target"] == "cat"


def test_extract_json_missing_raises():
    with pytest.raises(LLMError):
        extract_json_object("no json here")


def test_normalize_string_target_dedupe_and_clamp():
    p = normalize_parsed(
        {"target": ["Dog", " dog ", "cell_phone"], "effect": "BLUR", "intensity": 250}
    )
    assert p.target == ["dog", "cell phone"]
    assert p.effect == "blur"
    assert p.intensity == 100
    assert p.crop is False


def test_normalize_crop_effect_sets_crop_flag():
    p = normalize_parsed({"target": "person", "effect": "crop", "crop": False})
    assert p.target == ["person"]
    assert p.crop is True


def test_normalize_bad_intensity_defaults():
    p = normalize_parsed({"target": ["cat"], "effect": "remove_bg", "intensity": "강하게"})
    assert p.intensity == 15


@pytest.mark.parametrize(
    "raw",
    [
        {"target": ["dog"], "effect": "sharpen"},
        {"target": [], "effect": "blur"},
        {"target": 3, "effect": "blur"},
    ],
)
def test_normalize_invalid_raises(raw):
    with pytest.raises(LLMError):
        normalize_parsed(raw)


# --- provider 분기 ---


@pytest.mark.parametrize("provider", ["heuristic", "", "unknown-llm"])
def test_non_llm_provider_returns_none(provider, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("HTTP 호출되면 안 됨")

    monkeypatch.setattr(prompt_llm, "_post_json", boom)
    assert parse_prompt_llm("강아지만", _settings(LLM_PROVIDER=provider)) is None


def test_ollama_request_and_parse(monkeypatch):
    calls = {}

    def fake_post(url, payload, headers=None, timeout=30.0):
        calls.update(url=url, payload=payload, timeout=timeout)
        return {
            "message": {
                "content": '{"target": ["Dog"], "effect": "blur", "intensity": 40, "crop": false}'
            }
        }

    monkeypatch.setattr(prompt_llm, "_post_json", fake_post)
    s = _settings(LLM_BASE_URL="http://ollama:11434/", OLLAMA_MODEL="gemma4:e4b",
                  LLM_TIMEOUT_SECONDS=5)
    p = parse_prompt_llm("강아지만 남기고 배경 블러 강도 40", s)

    assert calls["url"] == "http://ollama:11434/api/chat"
    assert calls["payload"]["model"] == "gemma4:e4b"
    assert calls["payload"]["format"] == "json"
    assert calls["payload"]["stream"] is False
    assert calls["timeout"] == 5
    assert p.target == ["dog"] and p.effect == "blur" and p.intensity == 40


def test_openai_parse(monkeypatch):
    def fake_post(url, payload, headers=None, timeout=30.0):
        assert headers["Authorization"] == "Bearer sk-test"
        assert payload["response_format"] == {"type": "json_object"}
        return {"choices": [{"message": {"content": '{"target": ["car"], "effect": "crop"}'}}]}

    monkeypatch.setattr(prompt_llm, "_post_json", fake_post)
    p = parse_prompt_llm("차만 잘라줘", _settings(LLM_PROVIDER="openai", OPENAI_API_KEY="sk-test"))
    assert p.target == ["car"] and p.crop is True


def test_gemini_parse(monkeypatch):
    def fake_post(url, payload, headers=None, timeout=30.0):
        assert "gemini-2.0-flash:generateContent" in url
        assert headers["x-goog-api-key"] == "g-test"
        return {
            "candidates": [
                {"content": {"parts": [{"text": '{"target": ["cat"], "effect": "remove_bg"}'}]}}
            ]
        }

    monkeypatch.setattr(prompt_llm, "_post_json", fake_post)
    s = _settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="g-test", GEMINI_MODEL="gemini-2.0-flash")
    assert parse_prompt_llm("고양이만", s).target == ["cat"]


@pytest.mark.parametrize("provider", ["openai", "gemini"])
def test_cloud_provider_without_key_raises(provider, monkeypatch):
    monkeypatch.setattr(prompt_llm, "_post_json", lambda *a, **k: {})
    with pytest.raises(LLMError):
        parse_prompt_llm("강아지", _settings(LLM_PROVIDER=provider))


def test_malformed_response_raises(monkeypatch):
    monkeypatch.setattr(prompt_llm, "_post_json", lambda *a, **k: {"unexpected": 1})
    with pytest.raises(LLMError):
        parse_prompt_llm("강아지", _settings())


def test_connection_refused_raises_llm_error():
    # 닫힌 로컬 포트 → URLError → LLMError (실제 소켓, 외부 네트워크 없음)
    s = _settings(LLM_BASE_URL="http://127.0.0.1:9", LLM_TIMEOUT_SECONDS=2)
    with pytest.raises(LLMError):
        parse_prompt_llm("강아지", s)


# --- prompt_analyzer 노드 fallback ---


def test_prompt_analyzer_uses_llm_result(monkeypatch):
    nodes = pytest.importorskip("app.workflows.nodes")
    from app.schemas.request import ParsedPrompt

    monkeypatch.setattr(nodes, "get_settings", lambda: _settings(LLM_PROVIDER="ollama"))
    monkeypatch.setattr(
        nodes,
        "parse_prompt_llm",
        lambda prompt, settings: ParsedPrompt(target=["cup"], effect="blur"),
    )
    out = nodes.prompt_analyzer({"job_id": "j1", "prompt": "머그컵만 남겨"})
    assert out["parsed_prompt"]["target"] == ["cup"]
    assert out["prompt_parser"] == "ollama"


def test_prompt_analyzer_falls_back_on_llm_error(monkeypatch):
    nodes = pytest.importorskip("app.workflows.nodes")

    def fail(prompt, settings):
        raise LLMError("ollama down")

    monkeypatch.setattr(nodes, "get_settings", lambda: _settings(LLM_PROVIDER="ollama"))
    monkeypatch.setattr(nodes, "parse_prompt_llm", fail)
    out = nodes.prompt_analyzer({"job_id": "j2", "prompt": "강아지만 남기고 배경 블러"})
    assert out["prompt_parser"] == "heuristic"
    assert out["parsed_prompt"]["target"] == ["dog"]
    assert out["parsed_prompt"]["effect"] == "blur"


# --- selector · remove_object (인스턴스 선택 규격) ---


def test_normalize_selector_and_remove_object():
    p = normalize_parsed(
        {
            "target": ["person"],
            "effect": "remove_object",
            "selector": {"position": "Front", "count": "1", "attributes": ["Red Helmet", "red helmet"]},
        }
    )
    assert p.effect == "remove_object"
    assert p.selector.position == "front"
    assert p.selector.count == 1
    assert p.selector.attributes == ["red helmet"]


def test_normalize_selector_drops_bad_parts_only():
    """잘못된 position·count 는 버리고 target/effect 는 살린다."""
    p = normalize_parsed(
        {"target": ["dog"], "effect": "blur",
         "selector": {"position": "upstairs", "count": 0, "attributes": []}}
    )
    assert p.target == ["dog"] and p.selector is None


def test_normalize_null_selector():
    assert normalize_parsed({"target": ["cat"], "effect": "blur", "selector": None}).selector is None


def test_system_prompt_documents_keep_vs_remove():
    from app.services.prompt_spec import SYSTEM_PROMPT

    assert "remove_object" in SYSTEM_PROMPT and "selector" in SYSTEM_PROMPT


def test_lora_provider_without_base_model_raises():
    """LLM_PROVIDER=lora 인데 베이스 경로가 없으면 LLMError → 노드가 휴리스틱으로 fallback."""
    with pytest.raises(LLMError):
        parse_prompt_llm("강아지만 남겨", _settings(LLM_PROVIDER="lora", LORA_BASE_MODEL=""))


def test_lora_provider_missing_dir_raises(tmp_path):
    with pytest.raises(LLMError):
        parse_prompt_llm(
            "강아지만 남겨",
            _settings(LLM_PROVIDER="lora", LORA_BASE_MODEL=str(tmp_path / "nope")),
        )
