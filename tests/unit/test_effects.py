# -*- coding: utf-8 -*-
"""OpenCV 효과 모듈 스모크 (opencv 있을 때만).

작은 synthetic 이미지/마스크로 각 효과 함수 출력 shape 검증.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from app.schemas.request import ParsedPrompt
from app.services.effects import apply_blur, apply_crop, apply_remove_bg, refine_mask


@pytest.fixture
def sample_bgr():
    """80x80 BGR, 중앙 녹색 사각형."""
    img = np.zeros((80, 80, 3), dtype=np.uint8)
    img[20:60, 20:60] = (0, 255, 0)
    return img


@pytest.fixture
def sample_mask():
    """피사체 영역 255 마스크."""
    m = np.zeros((80, 80), dtype=np.uint8)
    m[20:60, 20:60] = 255
    return m


def test_refine_mask(sample_mask, sample_bgr):
    """정제 후에도 크기 유지, 마스크 비어 있지 않음."""
    out = refine_mask(sample_mask, sample_bgr)
    assert out.shape[:2] == sample_mask.shape[:2]
    assert out.any()


def test_remove_bg(sample_bgr, sample_mask):
    """배경 제거 결과는 BGRA(4채널)."""
    out = apply_remove_bg(sample_bgr, sample_mask)
    assert out.shape[2] == 4  # BGRA


def test_blur(sample_bgr, sample_mask):
    """블러 결과는 입력과 동일 shape."""
    out = apply_blur(sample_bgr, sample_mask, intensity=15)
    assert out.shape == sample_bgr.shape


def test_crop(sample_bgr, sample_mask):
    """크롭 결과는 원본보다 작거나 같음."""
    out = apply_crop(sample_bgr, sample_mask, padding=2)
    assert out.shape[0] <= sample_bgr.shape[0]
    assert out.shape[1] <= sample_bgr.shape[1]


def test_apply_effects_dispatch(sample_bgr, sample_mask):
    """ParsedPrompt.effect 디스패치 동작."""
    from app.services.effects import apply_effects

    parsed = ParsedPrompt(effect="blur", intensity=10)
    out = apply_effects(sample_bgr, sample_mask, parsed)
    assert out is not None
