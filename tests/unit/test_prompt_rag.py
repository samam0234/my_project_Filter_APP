# -*- coding: utf-8 -*-
"""프롬프트 해석 RAG 테스트 — 지식 베이스 적재 · 우선순위 · 검색 · 지시문 주입 · 재색인."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("pydantic_settings")
pytest.importorskip("loguru")

from app.core.config import Settings
from app.services import prompt_llm
from app.services.prompt_rag import (
    ExampleIndex,
    Hit,
    PromptRAG,
    format_examples,
    load_examples,
)

LEFT2_REMOVE = {"target": ["person"], "effect": "remove_object",
                "selector": {"position": "left", "rank": 2, "count": 1}}


def _seed(tmp_path, rows):
    f = tmp_path / "seed.jsonl"
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return f


def _feedback(folder, name, **payload):
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_load_examples_sources_and_priority(tmp_path):
    seed = _seed(tmp_path, [
        {"prompt": "강아지만 남기고 배경 블러", "parsed_prompt": {"target": ["dog"], "effect": "blur"}},
        {"prompt": "왼쪽에서 두 번째 사람 지워줘", "parsed_prompt": {"target": ["person"], "effect": "remove_bg"}},
    ])
    fb = tmp_path / "feedback"
    # 사용자 교정: 시드와 같은 문장 → 교정이 이긴다
    _feedback(fb, "a", vote="dislike", source="user", comment=json.dumps(LEFT2_REMOVE),
              meta={"prompt": "왼쪽에서 두 번째 사람 지워줘"})
    _feedback(fb, "b", vote="like", source="user",
              meta={"prompt": "고양이만 크롭", "parsed_prompt": {"target": ["cat"], "effect": "crop"}})
    _feedback(fb, "c", vote="dislike", source="user", comment="별로예요", meta={"prompt": "사람 지워"})  # 정답 없음
    _feedback(fb, "d", vote="dislike", source="pipeline_failure",
              meta={"prompt": "버스만", "parsed_prompt": {"target": ["bus"]}})  # 정답 불확실 → 제외

    examples = {e.prompt: e for e in load_examples(seed, fb)}
    assert set(examples) == {"강아지만 남기고 배경 블러", "왼쪽에서 두 번째 사람 지워줘", "고양이만 크롭"}
    corrected = examples["왼쪽에서 두 번째 사람 지워줘"]
    assert corrected.source == "correction"
    assert '"effect":"remove_object"' in corrected.answer and '"rank":2' in corrected.answer
    assert examples["고양이만 크롭"].source == "like"


def test_search_ranks_similar_prompt_first(tmp_path):
    seed = _seed(tmp_path, [
        {"prompt": "왼쪽에서 두 번째 사람 지워줘", "parsed_prompt": LEFT2_REMOVE},
        {"prompt": "강아지만 남기고 배경 블러", "parsed_prompt": {"target": ["dog"], "effect": "blur"}},
        {"prompt": "흰색 차 없애줘", "parsed_prompt": {"target": ["car"], "effect": "remove_object"}},
    ])
    index = ExampleIndex(load_examples(seed, None))
    hits = index.search("오른쪽에서 두 번째 사람 지워 줘", k=2)
    assert hits[0].example.prompt == "왼쪽에서 두 번째 사람 지워줘"
    assert hits[0].score > hits[1].score
    assert index.search("완전히 다른 문장 zzz", k=3, min_score=0.5) == []


def test_format_examples_block():
    from app.services.prompt_rag import Example

    block = format_examples([Hit(Example("흰색 차 없애줘", '{"target":["car"]}', "seed"), 0.8)])
    assert '"흰색 차 없애줘" -> {"target":["car"]}' in block
    assert format_examples([]) == ""


def test_examples_are_injected_into_llm_system_prompt(monkeypatch):
    sent = {}

    def fake_post(url, payload, headers=None, timeout=30.0):
        sent["system"] = payload["messages"][0]["content"]
        return {"message": {"content": '{"target": ["person"], "effect": "remove_object"}'}}

    monkeypatch.setattr(prompt_llm, "_post_json", fake_post)
    s = Settings.model_validate({"LLM_PROVIDER": "ollama"})
    prompt_llm.parse_prompt_llm("사람 지워", s, examples="\nEXAMPLE-BLOCK")
    assert sent["system"].startswith(prompt_llm.SYSTEM_PROMPT)
    assert sent["system"].endswith("EXAMPLE-BLOCK")


def _learning_db():
    from contextlib import contextmanager

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db.learning import LearningBase

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    LearningBase.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)

    @contextmanager
    def factory():
        with Session() as db:
            yield db

    return Session, factory


def _sample(db, prompt, answer, source="correction", status="pending"):
    from uuid import uuid4

    from app.models.learning_sample import LearningSample

    row = LearningSample(id=uuid4().hex, kind="prompt", source=source, status=status,
                         origin_id=uuid4().hex, prompt=prompt, answer=answer)
    db.add(row)
    db.commit()
    return row


def test_rag_uses_only_approved_samples_and_reindexes(tmp_path):
    """승인 전 교정은 쓰지 않고, 승인하면 다음 색인부터 쓰인다."""
    from app.services import learning_review

    Session, factory = _learning_db()
    s = Settings.model_validate({"PROMPT_RAG_REFRESH_SECONDS": 0})
    rag = PromptRAG(s, session_factory=factory)
    with Session() as db:
        pending = _sample(db, "왼쪽 두 번째 사람 삭제", LEFT2_REMOVE)
        _sample(db, "고양이만 크롭", {"target": ["cat"], "effect": "crop"}, source="request", status="approved")
        _sample(db, "버스만", {"target": ["bus"]}, source="pseudo_label", status="approved")  # 기본 출처 아님
    assert {e.prompt for e in rag.index().examples} == {"고양이만 크롭"}
    with Session() as db:
        learning_review.review(db, pending.id, "approve")
    assert {e.source for e in rag.index().examples} == {"correction", "request"}
    with Session() as db:
        learning_review.delete_sample(db, pending.id, s)
    assert [e.source for e in rag.index().examples] == ["request"]


def test_seed_is_used_only_when_listed(tmp_path):
    seed = _seed(tmp_path, [{"prompt": "강아지만 남겨", "parsed_prompt": {"target": ["dog"]}}])
    _, factory = _learning_db()
    default = Settings.model_validate({"PROMPT_RAG_SEED_FILE": str(seed)})
    with_seed = Settings.model_validate({"PROMPT_RAG_SEED_FILE": str(seed), "PROMPT_RAG_SOURCES": "correction,seed"})
    assert PromptRAG(default, session_factory=factory).index().examples == []
    assert [e.source for e in PromptRAG(with_seed, session_factory=factory).index().examples] == ["seed"]


def test_rag_survives_learning_db_outage():
    def broken():
        raise RuntimeError("learning db down")

    rag = PromptRAG(Settings.model_validate({}), session_factory=broken)
    assert rag.retrieve("사람 지워") == []


def test_prompt_analyzer_records_rag_sources_without_text(monkeypatch):
    nodes = pytest.importorskip("app.workflows.nodes")
    from app.schemas.request import ParsedPrompt
    from app.services.prompt_rag import Example

    class FakeRAG:
        def retrieve(self, prompt):
            return [Hit(Example("다른 사용자의 비밀 문장", '{"target":["person"]}', "correction"), 0.91)]

    seen = {}

    def fake_parse(prompt, settings, examples=""):
        seen["examples"] = examples
        return ParsedPrompt(target=["person"], effect="remove_object")

    monkeypatch.setattr(nodes, "get_settings", lambda: Settings.model_validate({"LLM_PROVIDER": "ollama"}))
    monkeypatch.setattr(nodes, "get_prompt_rag", lambda settings: FakeRAG())
    monkeypatch.setattr(nodes, "parse_prompt_llm", fake_parse)
    out = nodes.prompt_analyzer({"job_id": "r1", "prompt": "사람 지워"})
    assert "다른 사용자의 비밀 문장" in seen["examples"]  # LLM 에는 예시로 전달
    assert out["prompt_rag"] == [{"source": "correction", "score": 0.91}]  # meta 에는 원문 없음
