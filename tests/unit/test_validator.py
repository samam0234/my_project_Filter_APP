# -*- coding: utf-8 -*-
"""마스크 검증 로직 테스트."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("numpy")

from app.services.validator import mask_area_ratio, score_mask


def test_mask_area_ratio_empty():
    m = np.zeros((100, 100), dtype=np.uint8)
    assert mask_area_ratio(m) == 0.0


def test_mask_area_ratio_full():
    m = np.full((100, 100), 255, dtype=np.uint8)
    assert mask_area_ratio(m) == pytest.approx(1.0)


def test_score_mask_empty_failed():
    m = np.zeros((64, 64), dtype=np.uint8)
    r = score_mask(m, confidences=[0.9])
    assert r.ok is False
    assert r.status in {"failed", "fallback"}


def test_score_mask_reasonable_ok():
    m = np.zeros((100, 100), dtype=np.uint8)
    m[20:70, 20:70] = 255  # 25% area
    r = score_mask(m, confidences=[0.8, 0.9])
    assert r.ok is True
    assert r.status == "ok"
    assert 0.0 < r.quality_score <= 1.0
