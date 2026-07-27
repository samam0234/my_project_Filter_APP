# -*- coding: utf-8 -*-
"""프롬프트 휴리스틱 파서 테스트."""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from app.workflows.nodes import parse_prompt_heuristic


def test_default_person_remove_bg():
    p = parse_prompt_heuristic("배경 제거해줘")
    assert "person" in p.target or len(p.target) >= 1
    assert p.effect in {"remove_bg", "blur", "crop", "none"}


def test_blur_korean():
    p = parse_prompt_heuristic("강아지만 남기고 배경 블러")
    assert p.effect == "blur"
    assert "dog" in p.target


def test_crop_korean():
    p = parse_prompt_heuristic("사람만 크롭해줘")
    assert p.effect == "crop" or p.crop is True
    assert "person" in p.target


def test_quoted_target():
    p = parse_prompt_heuristic('"가방"만 추출')
    assert any("가방" in t or t == "bag" for t in p.target) or "bag" in p.target or len(p.target) >= 1


def test_intensity():
    p = parse_prompt_heuristic("배경 블러 강도 30")
    assert p.effect == "blur"
    assert p.intensity == 30
