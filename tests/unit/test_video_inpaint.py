# -*- coding: utf-8 -*-
"""영상 · GIF 대상 지우기 — 배경판(services/video_inpaint)."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")

from app.services import video_inpaint

H, W, N = 60, 120, 8


def _background():
    rng = np.random.default_rng(0)
    bg = rng.integers(40, 220, (H, W, 3), dtype=np.uint8)
    return bg


def _clip(moving: bool, pan: bool = False):
    bg = _background()
    wide = np.concatenate([bg, bg[:, ::-1]], axis=1)
    frames, masks = [], []
    for t in range(N):
        base = wide[:, t * 6: t * 6 + W].copy() if pan else bg.copy()
        x = 10 + t * 12 if moving else 50
        mask = np.zeros((H, W), np.uint8)
        mask[15:45, x: x + 14] = 255
        frame = base.copy()
        frame[mask > 0] = (255, 0, 255)  # 지울 대상
        frames.append(frame)
        masks.append(mask)
    return bg, frames, masks


def test_moving_object_is_replaced_by_real_background():
    bg, frames, masks = _clip(moving=True)
    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it), fill_unseen=lambda p, h: p)
    assert plan.static and plan.seen_ratio == 1.0
    out = video_inpaint.render(frames[3], 3, plan)
    hole = masks[3] > 0
    assert np.abs(out[hole].astype(int) - bg[hole].astype(int)).mean() < 1.0  # 실제 배경이 그대로
    assert not (out == (255, 0, 255)).all(axis=2).any()  # 대상 색이 남지 않음


def test_unseen_area_is_filled_once_and_reused():
    _, frames, masks = _clip(moving=False)
    calls = []

    def fill(plate, hole):
        calls.append(hole.sum())
        plate = plate.copy()
        plate[hole > 0] = (10, 20, 30)
        return plate

    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it), fill_unseen=fill)
    assert len(calls) == 1 and plan.seen_ratio < 0.5  # 안 보인 곳만, 한 번만
    a, b = video_inpaint.render(frames[0], 0, plan), video_inpaint.render(frames[5], 5, plan)
    hole = masks[0] > 0
    assert (a[hole] == b[hole]).all()  # 프레임마다 같게 메움 → 깜빡임 없음


def test_panning_camera_falls_back_to_per_frame():
    _, frames, masks = _clip(moving=False, pan=True)
    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it))
    assert plan.static is False and plan.plate is None
    out = video_inpaint.render(frames[2], 2, plan)
    assert out.shape == frames[2].shape
