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


def test_unalignable_moving_camera_falls_back_to_per_frame():
    """잡음뿐인 작은 화면이 움직이면 특징점으로 맞출 수 없다 → 예전처럼 프레임마다 Telea."""
    _, frames, masks = _clip(moving=False, pan=True)
    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it))
    assert plan.mode == "frame" and plan.static is False and plan.plate is None
    out = video_inpaint.render(frames[2], 2, plan)
    assert out.shape == frames[2].shape


def _scene(h=240, w=900, seed=1):
    """특징점이 잡히는 무늬 배경 (사각형 · 원 · 글자)."""
    import cv2

    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), 120, np.uint8)
    for _ in range(160):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        color = tuple(int(c) for c in rng.integers(0, 255, 3))
        if rng.random() < 0.5:
            cv2.rectangle(img, (x, y), (x + int(rng.integers(8, 40)), y + int(rng.integers(8, 40))), color, -1)
        else:
            cv2.circle(img, (x, y), int(rng.integers(4, 20)), color, -1)
    for i in range(0, w, 60):
        cv2.putText(img, str(i), (i, 30 + (i % 7) * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return img


def _pan_clip(n=16, side=360, step=8, parallax=False):
    """카메라가 옆으로 움직이고(배경이 step px 씩 왼쪽으로 밀림) 대상은 오른쪽으로 걷는다. truth 는 프레임마다 정답 배경."""
    far = _scene()
    near = _scene(seed=7)
    frames, masks, truths = [], [], []
    for t in range(n):
        base = far[:, t * step: t * step + side].copy()
        if parallax:  # 아래쪽 절반은 3배 빠르게 움직이는 가까운 층 — 한 평면으로 맞출 수 없다
            base[120:] = near[120:, t * step * 3: t * step * 3 + side]
        mask = np.zeros(base.shape[:2], np.uint8)
        x = 60 + t * 12  # 배경은 왼쪽으로 밀리고 대상은 오른쪽으로 — 세상 기준으로 움직여 뒤가 보인다
        mask[60:200, x: x + 40] = 255
        frame = base.copy()
        frame[mask > 0] = (255, 0, 255)
        frames.append(frame)
        masks.append(mask)
        truths.append(base)
    return frames, masks, truths


def test_panning_camera_uses_aligned_plate():
    """카메라가 옆으로 움직여도 프레임을 맞춰 모은 배경판으로 실제 배경이 돌아온다."""
    frames, masks, truths = _pan_clip()
    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it), fill_unseen=lambda p, h: p)
    assert plan.mode == "aligned" and plan.static and plan.seen_ratio > 0.9
    errs = []
    for i in (3, 8, 12):
        out = video_inpaint.render(frames[i], i, plan)
        hole = masks[i] > 0
        assert not (out[hole] == (255, 0, 255)).all(axis=1).any()  # 대상 색이 남지 않음
        errs.append(np.abs(out[hole].astype(int) - truths[i][hole].astype(int)).mean())
    assert np.mean(errs) < 12  # 맞추기 보간 오차 정도만 (Telea 는 수십)


def test_parallax_scene_does_not_use_aligned_plate():
    """앞뒤 층이 다른 속도로 움직이면(시차) 한 번에 맞출 수 없다 → 배경판 대신 프레임마다."""
    frames, masks, _ = _pan_clip(parallax=True)
    it = iter(masks)
    plan = video_inpaint.build_plan(frames, lambda f: next(it), fill_unseen=lambda p, h: p)
    assert plan.mode == "frame"
