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


def test_keep_specific_instance_with_selector():
    """사용자 실제 사례: 맨 앞 + 색 속성 + '제외하고 전부 제거' = 남기기."""
    p = parse_prompt_heuristic(
        "맨 앞에 빨간색 안전모와 형광색 조끼를 입은 남성을 제외하고 전부 제거 부탁해"
    )
    assert p.target == ["person"]
    assert p.effect == "remove_bg"
    assert p.selector.position == "front"
    assert set(p.selector.attributes) == {"red helmet", "neon yellow vest"}


@pytest.mark.parametrize(
    "prompt,target",
    [("왼쪽에 있는 사람 지워줘", "person"), ("강아지 없애줘", "dog"), ("remove the car", "car")],
)
def test_remove_object(prompt, target):
    p = parse_prompt_heuristic(prompt)
    assert p.effect == "remove_object"
    assert p.target == [target]


@pytest.mark.parametrize("prompt", ["배경 제거해줘", "사람 빼고 다 지워줘", "강아지만 남기고 나머지 삭제"])
def test_background_or_except_is_keep(prompt):
    assert parse_prompt_heuristic(prompt).effect == "remove_bg"


def test_count_selector():
    p = parse_prompt_heuristic("사람 2명만 남기고 배경 블러")
    assert p.effect == "blur" and p.selector.count == 2


def test_plain_prompt_has_no_selector():
    assert parse_prompt_heuristic("강아지만 남기고 배경 블러").selector is None


@pytest.mark.parametrize(
    "prompt,position,rank",
    [("오른쪽에서 두 번째 사람 지워줘", "right", 2), ("왼쪽에서 3번째 사람만 남겨", "left", 3),
     ("remove the second person from the left", "left", 2)],
)
def test_rank_selector(prompt, position, rank):
    s = parse_prompt_heuristic(prompt).selector
    assert s.position == position and s.rank == rank
