# -*- coding: utf-8 -*-
"""세그 라벨링 묶음 (scripts/seg_labeling.py) — 사례 고르기 · 라벨 검사 · 클래스 순서 맞추기. 모델 없이."""

from __future__ import annotations

import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("seg_labeling", REPO_ROOT / "scripts/seg_labeling.py")
seg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seg)


def _case(folder: Path, stem: str, payload: dict, image: bool = True) -> None:
    (folder / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    if image:
        (folder / f"{stem}.jpg").write_bytes(b"\xff\xd8fake")


def test_pick_cases_only_failures_and_dislikes_with_images(tmp_path):
    _case(tmp_path, "a", {"vote": "dislike", "source": "pipeline_failure", "prompt": "강아지만"})
    _case(tmp_path, "b", {"vote": "dislike", "source": "user", "prompt": "사람만"})
    _case(tmp_path, "c", {"vote": "like", "source": "user", "prompt": "고양이만"})
    _case(tmp_path, "d", {"vote": "dislike", "source": "user"}, image=False)
    picked = {c.case_id for c in seg.pick_cases(tmp_path)}
    assert picked == {"a", "b"}
    assert {c.case_id for c in seg.pick_cases(tmp_path, include_likes=True)} == {"a", "b", "c"}


def _folder(tmp_path, lines: str, classes: list[str] | None = None) -> Path:
    root = tmp_path / "fixed"
    (root / "images").mkdir(parents=True)
    (root / "labels").mkdir()
    (root / "images" / "x.jpg").write_bytes(b"img")
    (root / "labels" / "x.txt").write_text(lines, encoding="utf-8")
    if classes:
        (root / "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
    return root


def _args(root, fix=False):
    return Namespace(folder=root, classes=80, model=None, fix=fix)


def test_check_accepts_valid_and_rejects_broken_labels(tmp_path):
    ok = _folder(tmp_path, "0 0.1 0.1 0.5 0.1 0.3 0.6\n")
    assert seg.check(_args(ok)) == 0
    bad = _folder(tmp_path / "b", "85 0.1 0.1 0.5 0.1 0.3 0.6\n0 0.1 0.1 1.5 0.1 0.3 0.6\n0 0.1 0.1\n")
    assert seg.check(_args(bad)) == 1


def test_class_order_from_labeling_tool_is_remapped(tmp_path, monkeypatch):
    names = ["person", "bicycle", "car", "dog"]
    monkeypatch.setattr(seg, "model_names", lambda model=None: names)
    assert seg.remap_table(["person", "bicycle"], names) is None  # 같은 순서
    assert seg.remap_table(["dog", "person"], names) == {0: 3, 1: 0}
    with pytest.raises(ValueError):
        seg.remap_table(["unicorn"], names)
    root = _folder(tmp_path, "0 0.1 0.1 0.5 0.1 0.3 0.6\n1 0.2 0.2 0.4 0.2 0.3 0.5\n", classes=["dog", "person"])
    assert seg.check(_args(root)) == 1  # 순서가 달라 그냥은 통과시키지 않는다
    assert seg.check(_args(root, fix=True)) == 0
    first = [l.split()[0] for l in (root / "labels" / "x.txt").read_text(encoding="utf-8").splitlines()]
    assert first == ["3", "0"]
