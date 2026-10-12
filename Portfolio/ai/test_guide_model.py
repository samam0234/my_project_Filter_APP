import pytest

pytest.importorskip("langchain_ollama")

from guide_graph import DEFAULT_MODEL, guide_model


def test_default_is_e4b_and_only_12b_is_the_high_choice():
    assert guide_model(None) == "gemma4:e4b"
    assert guide_model("") == DEFAULT_MODEL
    assert guide_model("gemma4:e4b") == "gemma4:e4b"
    assert guide_model("gemma4:12b") == "gemma4:12b"
    assert guide_model("qwen3.8:27b") == "gemma4:e4b"
    assert guide_model("gemma4:12b; rm") == "gemma4:e4b"
