# -*- coding: utf-8 -*-
"""인스턴스 선택(위치·개수·색 속성) 테스트 — 합성 이미지, 모델 불필요."""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")
pytest.importorskip("pydantic")

from app.schemas.request import InstanceSelector
from app.services.instance_selector import parse_attribute, select_instances
from app.services.segmentation import Instance

H, W = 200, 300


def _rect(x0, y0, x1, y1, label="person", conf=0.9) -> Instance:
    m = np.zeros((H, W), np.uint8)
    m[y0:y1, x0:x1] = 255
    return Instance.from_mask(m, label, conf)


def _scene():
    """왼쪽 작은 사람(뒤) · 가운데 큰 사람(앞, 빨간 머리) · 오른쪽 중간 사람."""
    img = np.full((H, W, 3), 120, np.uint8)
    left = _rect(10, 40, 50, 120)
    front = _rect(110, 20, 190, 195)
    right = _rect(230, 50, 290, 150)
    img[20:55, 110:190] = (0, 0, 230)  # BGR 빨강 — front 의 머리(상단) 영역
    img[70:130, 230:290] = (230, 60, 0)  # 파랑 — right 의 상의 영역
    return img, [left, front, right]


def _pick(selector, scene=None):
    img, inst = scene or _scene()
    return [inst.index(c) for c in select_instances(inst, selector, img).chosen]


def test_no_selector_keeps_all():
    assert _pick(None) == [0, 1, 2]


@pytest.mark.parametrize(
    "position,expected",
    [("front", [1]), ("back", [0]), ("left", [0]), ("right", [2]),
     ("center", [1]), ("largest", [1]), ("smallest", [0])],
)
def test_position_picks_one(position, expected):
    assert _pick(InstanceSelector(position=position)) == expected


def test_count_with_position():
    assert _pick(InstanceSelector(position="left", count=2)) == [0, 1]


def test_count_only_prefers_largest():
    assert _pick(InstanceSelector(count=2)) == [1, 2]


def test_color_attribute_with_part():
    assert _pick(InstanceSelector(attributes=["red helmet"])) == [1]
    assert _pick(InstanceSelector(attributes=["blue shirt"])) == [2]


def test_color_attribute_then_position():
    """속성 통과 후보 안에서 위치 정렬."""
    img, inst = _scene()
    img[40:60, 10:50] = (0, 0, 230)  # left 도 빨간 머리
    both = [inst.index(c) for c in select_instances(
        inst, InstanceSelector(attributes=["red hat"]), img).chosen]
    assert sorted(both) == [0, 1]
    left = [inst.index(c) for c in select_instances(
        inst, InstanceSelector(position="left", attributes=["red hat"]), img).chosen]
    assert left == [0]


def test_unmatched_attribute_falls_back_to_best_one():
    r = select_instances(_scene()[1], InstanceSelector(attributes=["green vest"]), _scene()[0])
    assert len(r.chosen) == 1
    assert r.attribute_matched is False


def test_unknown_attribute_is_ignored():
    """색이 없는 속성("tall")은 무시 → 전부 유지."""
    assert _pick(InstanceSelector(attributes=["tall"])) == [0, 1, 2]


@pytest.mark.parametrize(
    "phrase,expected",
    [("red helmet", ("red", "helmet")), ("neon yellow vest", ("neon yellow", "vest")),
     ("neon vest", ("neon yellow", "vest")), ("white car", ("white", None)),
     ("grey jacket", ("gray", "jacket")), ("tall", (None, None))],
)
def test_parse_attribute(phrase, expected):
    assert parse_attribute(phrase) == expected


def test_rank_along_position():
    """오른쪽에서 두 번째 → right 정렬의 2번째."""
    assert _pick(InstanceSelector(position="right", rank=2)) == [1]
    assert _pick(InstanceSelector(position="left", rank=3)) == [2]


def test_rank_beyond_candidates_picks_last():
    assert _pick(InstanceSelector(position="left", rank=9)) == [2]
