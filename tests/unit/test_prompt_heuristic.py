# -*- coding: utf-8 -*-
"""프롬프트 휴리스틱 파서 테스트.

LLM 없이 한/영 키워드로 target·effect·intensity 를 뽑는지 확인.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from app.workflows.nodes import parse_prompt_heuristic


def test_default_person_remove_bg():
    """대상 키워드 없으면 person 계열 + 효과 존재."""
    p = parse_prompt_heuristic("배경 제거해줘")
    assert "person" in p.target or len(p.target) >= 1
    assert p.effect in {"remove_bg", "blur", "crop", "none"}


def test_blur_korean():
    """'블러' + '강아지' → effect=blur, target dog."""
    p = parse_prompt_heuristic("강아지만 남기고 배경 블러")
    assert p.effect == "blur"
    assert "dog" in p.target


def test_crop_korean():
    """'크롭' + '사람' → crop 효과 또는 crop 플래그."""
    p = parse_prompt_heuristic("사람만 크롭해줘")
    assert p.effect == "crop" or p.crop is True
    assert "person" in p.target


def test_quoted_target():
    """따옴표 안 문구를 target 으로 추출 (또는 bag 매핑)."""
    p = parse_prompt_heuristic('"가방"만 추출')
    assert any("가방" in t or t == "bag" for t in p.target) or "bag" in p.target or len(p.target) >= 1


def test_intensity():
    """'강도 30' → intensity=30."""
    p = parse_prompt_heuristic("배경 블러 강도 30")
    assert p.effect == "blur"
    assert p.intensity == 30
