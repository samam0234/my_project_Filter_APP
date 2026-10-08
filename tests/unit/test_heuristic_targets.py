# -*- coding: utf-8 -*-
"""LLM 이 꺼졌을 때의 키워드 파서 — 지정한 대상만 뽑는가 ("X 말고 Y만", 풍경, 영어, 한 글자 낱말 오탐)."""

from __future__ import annotations

import pytest

from app.services.heuristic_targets import detect_targets, find_mentions
from app.workflows.nodes import parse_prompt_heuristic


@pytest.mark.parametrize(
    "text, expected",
    [
        # 남길 것만 — 같이 언급된 다른 물체는 대상이 아니다
        ("강아지만 남기고 사람은 지워줘", ["dog"]),
        ("사람 말고 강아지만 남겨줘", ["dog"]),
        ("차는 빼고 사람만 남겨줘", ["person"]),
        ("개 말고 고양이만 남기고 배경 블러", ["cat"]),
        ("의자랑 배경은 지우고 사람만 남겨줘", ["person"]),
        ("자전거는 놔두고 사람만 남겨줘", ["person"]),
        ("잔디는 그대로 두고 사람만 남겨줘", ["person"]),
        # 이어진 언급은 같이 남긴다
        ("강아지, 고양이만 남기고 사람은 다 지워줘", ["dog", "cat"]),
        ("사람이랑 강아지만 남기고 나머지는 블러", ["person", "dog"]),
        ("자동차랑 버스만 남기고 사람은 지워줘", ["car", "bus"]),
        # 지울 대상
        ("강아지 지워줘", ["dog"]),
        ("사진에서 강아지만 지워줘 사람은 그대로 두고", ["dog"]),
        ("자동차만 지워줘 사람은 건드리지 말고", ["car"]),
        # "X 빼고 다 지워" — 빼는 쪽이 남길 대상
        ("사람 빼고 다 지워줘", ["person"]),
        ("트럭을 제외한 모든 것을 투명하게", ["truck"]),
        # 풍경
        ("건물만 남기고 사람이랑 차는 지워줘", ["building"]),
        ("산이랑 하늘만 남기고 나머지 지워줘", ["mountain", "sky"]),
        ("도로 말고 건물만 남겨줘", ["building"]),
        # 영어 — 동사가 앞에 온다
        ("keep only the dog and remove the people", ["dog"]),
        ("blur the background but keep the cat sharp, ignore the chairs", ["cat"]),
        ("keep the car and the bus, get rid of the trees", ["car", "bus"]),
        ("remove the car but don't touch the person", ["car"]),
        # 언급이 없으면 사람
        ("배경 블러", ["person"]),
    ],
)
def test_targets(text, expected):
    assert detect_targets(text.lower()) == expected


@pytest.mark.parametrize(
    "text",
    [
        "사람만 남기고 배경 블러 강도 50",  # "강도" 의 "강" 이 강(river)으로 잡히던 것
        "산책하는 사람만 남겨줘",  # "산책" 의 "산"
        "물건 말고 사람만 남겨줘",  # "물건" 의 "물"
        "차이가 큰 사람만 남겨줘",  # "차이" 의 "차"
    ],
)
def test_one_character_words_inside_other_words_are_not_objects(text):
    assert detect_targets(text) == ["person"]


def test_longest_surface_form_wins_and_does_not_double_count():
    assert [m[2] for m in find_mentions("자동차만 남겨줘")] == ["car"]  # "차" 가 또 잡히지 않는다
    assert [m[2] for m in find_mentions("머그컵만")] == ["cup"]


def test_full_heuristic_parser_uses_it():
    parsed = parse_prompt_heuristic("강아지만 남기고 사람은 지워줘")
    assert parsed.target == ["dog"] and parsed.effect == "remove_bg"
    erase = parse_prompt_heuristic("차는 지워줘 사람은 건드리지 말고")
    assert erase.target == ["car"] and erase.effect == "remove_object"
    quoted = parse_prompt_heuristic('"traffic light" 만 남겨줘')
    assert quoted.target == ["traffic light"]  # 따옴표는 그대로 (예전 동작)
