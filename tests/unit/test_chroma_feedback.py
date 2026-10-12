# -*- coding: utf-8 -*-
"""루트 data/chroma — 확인된 피드백만 색인하고, 먼 문장은 예시로 꺼내지 않는다."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("chromadb")

from scripts.chroma_embed import cosine
from scripts.chroma_feedback import load_verified, rebuild, search


def _write(folder: Path, name: str, payload: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_char_vector_ranks_similar_korean_higher():
    close = cosine("왼쪽에서 두 번째 사람 지워줘", "오른쪽에서 두 번째 사람 지워 줘")
    far = cosine("왼쪽에서 두 번째 사람 지워줘", "강아지만 남기고 배경 블러")
    assert close > far
    assert close > 0.45


def test_rebuild_keeps_verified_feedback_only(tmp_path):
    feedback = tmp_path / "feedback"
    store = tmp_path / "chroma"
    _write(
        feedback,
        "fix.json",
        {
            "vote": "dislike",
            "source": "user",
            "comment": json.dumps({"target": ["person"], "effect": "remove_object"}),
            "meta": {"prompt": "왼쪽에서 두 번째 사람 지워줘"},
        },
    )
    _write(
        feedback,
        "like.json",
        {
            "vote": "like",
            "source": "user",
            "meta": {"prompt": "고양이만 크롭", "parsed_prompt": {"target": ["cat"], "effect": "crop"}},
        },
    )
    _write(
        feedback,
        "fail.json",
        {
            "vote": "dislike",
            "source": "pipeline_failure",
            "meta": {"prompt": "버스만", "parsed_prompt": {"target": ["bus"]}},
        },
    )
    _write(feedback, "empty.json", {"vote": "dislike", "comment": "별로예요", "meta": {"prompt": "사람 지워"}})

    rows = {row["prompt"]: row for row in load_verified(feedback)}
    assert set(rows) == {"왼쪽에서 두 번째 사람 지워줘", "고양이만 크롭"}
    assert rows["왼쪽에서 두 번째 사람 지워줘"]["source"] == "correction"
    assert rebuild(feedback, store) == 2

    hits = search("오른쪽에서 두 번째 사람 지워 줘", k=2, min_similarity=0.4, store=store)
    assert hits
    assert hits[0]["prompt"] == "왼쪽에서 두 번째 사람 지워줘"
    assert hits[0]["source"] == "correction"
    assert search("완전히 다른 외계 문장 zzz qqq", k=3, min_similarity=0.85, store=store) == []

    feedback.joinpath("fix.json").unlink()
    assert rebuild(feedback, store) == 1
    again = search("왼쪽에서 두 번째 사람 지워줘", k=3, min_similarity=0.0, store=store)
    assert [hit["prompt"] for hit in again] == ["고양이만 크롭"]
