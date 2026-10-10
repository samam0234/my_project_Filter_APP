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


def test_remove_object_fills_masked_region():
    """지운 영역이 주변 배경색으로 채워지고 크기는 유지."""
    from app.services.effects import apply_remove_object

    img = np.full((80, 120, 3), (40, 160, 40), np.uint8)
    img[20:60, 40:80] = (0, 0, 255)  # 지울 빨간 물체
    mask = np.zeros((80, 120), np.uint8)
    mask[20:60, 40:80] = 255
    out = apply_remove_object(img, mask)
    assert out.shape == img.shape
    center = out[35:45, 55:65].reshape(-1, 3).mean(axis=0)
    assert center[2] < 120 and center[1] > 100  # 빨강이 사라지고 초록 배경에 가까움
    assert (out[0:10, 0:10] == img[0:10, 0:10]).all()  # 마스크 밖은 그대로


def test_refine_mask_does_not_grab_far_regions():
    """GrabCut 이 비슷한 색의 떨어진 영역을 전경으로 붙이지 않는다."""
    from app.services.effects import refine_mask

    img = np.full((100, 160, 3), 90, np.uint8)
    img[30:70, 20:60] = (255, 255, 255)   # 선택한 흰 물체
    img[30:70, 110:150] = (255, 255, 255)  # 멀리 떨어진 같은 색 물체
    mask = np.zeros((100, 160), np.uint8)
    mask[30:70, 20:60] = 255
    refined = refine_mask(mask, img)
    assert not refined[:, 100:].any()
