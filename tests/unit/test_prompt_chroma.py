# -*- coding: utf-8 -*-
"""문장 해석 Chroma — 글자 검색이 놓친 확인 문장 한 건을 보탠다."""

from __future__ import annotations

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("pydantic_settings")

from app.core.config import Settings
from app.services.prompt_chroma import APPROVED, VERIFIED, merge_hits, search_store, sync_examples
from app.services.prompt_rag import Example, Hit, PromptRAG


def test_merge_keeps_lexical_order_and_one_new_verified_hit():
    lexical = [
        Hit(Example("강아지만 남기고 배경 블러", '{"effect":"blur"}', "like"), 0.81),
        Hit(Example("흰색 차 없애줘", '{"effect":"remove_object"}', "request"), 0.7),
    ]
    vector = [
        Hit(Example("강아지만 남기고 배경 블러", '{"effect":"blur"}', "like"), 0.99),
        Hit(Example("왼쪽에서 두 번째 사람 지워줘", '{"effect":"remove_object"}', "correction"), 0.88),
    ]
    merged = merge_hits(lexical, vector, k=2)
    assert [hit.example.prompt for hit in merged] == [
        "강아지만 남기고 배경 블러",
        "흰색 차 없애줘",
        "왼쪽에서 두 번째 사람 지워줘",
    ]
    assert merge_hits(lexical, [], k=2) == lexical


def test_store_roundtrip_and_retrieve_when_learning_db_is_down(tmp_path):
    shared = tmp_path / "shared"
    runtime = tmp_path / "runtime"
    example = Example("왼쪽에서 두 번째 사람 지워줘", '{"target":["person"],"effect":"remove_object"}', "correction")
    sync_examples(shared, [example], VERIFIED)
    hits = search_store(shared, "오른쪽에서 두 번째 사람 지워 줘", VERIFIED, k=1, min_similarity=0.4)
    assert hits[0].example.answer.startswith('{"target":["person"]')
    assert search_store(shared, "완전히 다른 외계 문장 zzz", VERIFIED, k=2, min_similarity=0.85) == []

    def broken():
        raise RuntimeError("learning db down")

    settings = Settings.model_validate({
        "PROMPT_CHROMA_ENABLED": True,
        "PROMPT_CHROMA_DIR": str(runtime),
        "PROMPT_CHROMA_SHARED_DIR": str(shared),
        "PROMPT_CHROMA_MIN_SCORE": 0.4,
        "PROMPT_RAG_REFRESH_SECONDS": 0,
    })
    found = PromptRAG(settings, session_factory=broken).retrieve("오른쪽에서 두 번째 사람 지워 줘")
    assert found[0].example.prompt == example.prompt
    assert found[0].example.source == "correction"
    assert search_store(runtime, example.prompt, APPROVED, k=1, min_similarity=0.99) == []
