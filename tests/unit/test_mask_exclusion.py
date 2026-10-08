# -*- coding: utf-8 -*-
"""지정하지 않은 사람·동물·물체가 대상에 붙어 남는 것을 막는 규칙 — 겹침 소유권 · 금지 구역 · 정제 기본값."""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from app.core.config import Settings
from app.services.effects import refine_mask
from app.services.mask_exclusion import (
    exclusive_mask,
    finalize_selection,
    forbid_zone,
    rest_instances,
)
from app.services.segmentation import Instance, SegmentationResult

H, W = 100, 200


def _inst(x0, x1, label="person", conf=0.9, y0=10, y1=90) -> Instance:
    m = np.zeros((H, W), np.uint8)
    m[y0:y1, x0:x1] = 255
    return Instance.from_mask(m, label, conf)


def _area(mask) -> int:
    return int(np.count_nonzero(mask))


def test_defaults_come_from_the_experiments():
    s = Settings.model_validate({"DB_DIALECT": "sqlite"})
    assert (s.mask_exclusive, s.mask_grabcut, s.preprocess_clahe, s.mask_forbid_refine) == ("subtract", False, False, False)


def test_subtract_removes_pixels_owned_by_other_instances():
    left = _inst(20, 100)  # 선택한 사람
    right = _inst(90, 170)  # 옆 사람 — 90~100 이 겹침
    out = exclusive_mask([left], [right], (H, W), "subtract")
    assert out[50, 50] == 255 and out[50, 95] == 0 and out[50, 130] == 0
    assert _area(out) == (90 - 20) * 80


def test_off_keeps_the_old_behaviour():
    left, right = _inst(20, 100), _inst(90, 170)
    assert _area(exclusive_mask([left], [right], (H, W), "off")) == _area(left.mask)


def test_conf_rule_lets_the_more_confident_instance_keep_the_overlap():
    chosen, rival = _inst(20, 100, conf=0.8), _inst(90, 170, conf=0.95)
    assert exclusive_mask([chosen], [rival], (H, W), "conf")[50, 95] == 0  # 이웃이 더 확실 → 이웃 몫
    sure = _inst(20, 100, conf=0.95)
    weak = _inst(90, 170, conf=0.6)
    assert exclusive_mask([sure], [weak], (H, W), "conf")[50, 95] == 255  # 대상이 더 확실 → 대상 몫


def test_front_rule_gives_overlap_to_the_instance_closer_to_the_camera():
    far = _inst(20, 100, y0=10, y1=60)  # 아래 끝 60
    near = _inst(90, 170, y0=30, y1=95)  # 아래 끝 95 — 더 가깝다
    assert exclusive_mask([far], [near], (H, W), "front")[40, 95] == 0
    assert exclusive_mask([near], [far], (H, W), "front")[40, 95] == 255


def test_never_deletes_most_of_the_target():
    """다른 인스턴스가 대상 대부분을 덮어도(검출 오류) 대상을 통째로 잃지 않는다."""
    target = _inst(20, 100)
    swallow = _inst(20, 95)  # 대상의 94% 를 덮는 다른 인스턴스
    assert _area(exclusive_mask([target], [swallow], (H, W), "subtract")) == _area(target.mask)


def test_small_islands_left_after_subtracting_are_dropped():
    target = _inst(20, 100)
    cut = np.zeros((H, W), np.uint8)
    cut[:, 70:98] = 255  # 가운데를 도려내면 큰 덩어리(왼쪽 50px, 62%)와 오른쪽 2px 조각(약 2.5%)이 남는다
    other = Instance.from_mask(cut, "dog", 0.9)
    out = exclusive_mask([target], [other], (H, W), "subtract")
    assert out[50, 25] == 255 and out[50, 99] == 0  # 큰 쪽만 남고 2px 섬은 정리


def test_forbid_zone_keeps_the_targets_core_free():
    chosen = _inst(20, 100)
    zone = forbid_zone(chosen.mask, [_inst(90, 170)])
    assert zone is not None
    assert zone[50, 130] == 255  # 이웃 안쪽은 금지
    assert zone[50, 60] == 0  # 대상 한가운데는 절대 금지 아님
    assert forbid_zone(chosen.mask, []) is None


def test_refine_removes_forbidden_pixels_even_without_grabcut():
    mask = np.zeros((H, W), np.uint8)
    mask[10:90, 20:120] = 255
    forbid = np.zeros((H, W), np.uint8)
    forbid[:, 100:] = 255
    out = refine_mask(mask, np.full((H, W, 3), 90, np.uint8), forbid)
    assert out[50, 60] == 255 and not out[:, 105:].any()


def test_grabcut_is_opt_in_and_respects_forbidden_zone():
    img = np.full((H, W, 3), 60, np.uint8)
    img[10:90, 20:120] = (200, 200, 200)
    mask = np.zeros((H, W), np.uint8)
    mask[10:90, 20:100] = 255
    forbid = np.zeros((H, W), np.uint8)
    forbid[:, 100:] = 255  # 오른쪽 20px 는 이웃 구역 — 색이 비슷해도 가져오면 안 된다
    plain = refine_mask(mask, img, None, use_grabcut=False)
    assert _area(plain) <= _area(mask) + 400  # 모폴로지만: 거의 그대로
    grabbed = refine_mask(mask, img, forbid, use_grabcut=True)
    assert not grabbed[:, 101:].any()


def test_finalize_selection_uses_other_classes_and_unchosen_instances():
    s = Settings.model_validate({"DB_DIALECT": "sqlite"})
    a, b = _inst(20, 100), _inst(90, 170)
    bag = _inst(60, 110, label="handbag", conf=0.9, y0=40, y1=80)
    seg = SegmentationResult(mask=np.zeros((H, W), np.uint8), instances=[a, b], others=[bag])
    mask, forbid = finalize_selection(seg, [a], (H, W), s)
    assert mask[20, 30] == 255  # 대상 위쪽은 그대로
    assert mask[60, 105] == 0 and mask[60, 80] == 0  # 이웃·가방이 차지한 곳은 대상이 아니다
    assert forbid is None  # 금지 구역은 MASK_FORBID_REFINE 일 때만
    on = Settings.model_validate({"DB_DIALECT": "sqlite", "MASK_FORBID_REFINE": True})
    assert finalize_selection(seg, [a], (H, W), on)[1] is not None
    # 선택 없음(클래스 전체)이면 같은 클래스 인스턴스는 모두 대상 — 다른 클래스(가방)만 덜어낸다
    all_mask, _ = finalize_selection(seg, [a, b], (H, W), s)
    assert all_mask[20, 130] == 255 and all_mask[60, 80] == 0


def test_rest_instances_excludes_chosen_only():
    a, b = _inst(20, 100), _inst(90, 170)
    other = _inst(0, 10, label="dog")
    rest = rest_instances([a, b], [a], [other])
    assert len(rest) == 2 and a not in rest and b in rest and other in rest
