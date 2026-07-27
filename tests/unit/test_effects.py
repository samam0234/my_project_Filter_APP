# -*- coding: utf-8 -*-
"""OpenCV 효과 모듈 스모크 (opencv 있을 때만)."""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from app.schemas.request import ParsedPrompt
from app.services.effects import apply_blur, apply_crop, apply_remove_bg, refine_mask


@pytest.fixture
def sample_bgr():
    img = np.zeros((80, 80, 3), dtype=np.uint8)
    img[20:60, 20:60] = (0, 255, 0)
    return img


@pytest.fixture
def sample_mask():
    m = np.zeros((80, 80), dtype=np.uint8)
    m[20:60, 20:60] = 255
    return m


def test_refine_mask(sample_mask, sample_bgr):
    out = refine_mask(sample_mask, sample_bgr)
    assert out.shape[:2] == sample_mask.shape[:2]
    assert out.any()


def test_remove_bg(sample_bgr, sample_mask):
    out = apply_remove_bg(sample_bgr, sample_mask)
    assert out.shape[2] == 4  # BGRA


def test_blur(sample_bgr, sample_mask):
    out = apply_blur(sample_bgr, sample_mask, intensity=15)
    assert out.shape == sample_bgr.shape


def test_crop(sample_bgr, sample_mask):
    out = apply_crop(sample_bgr, sample_mask, padding=2)
    assert out.shape[0] <= sample_bgr.shape[0]
    assert out.shape[1] <= sample_bgr.shape[1]


def test_apply_effects_dispatch(sample_bgr, sample_mask):
    from app.services.effects import apply_effects

    parsed = ParsedPrompt(effect="blur", intensity=10)
    out = apply_effects(sample_bgr, sample_mask, parsed)
    assert out is not None
