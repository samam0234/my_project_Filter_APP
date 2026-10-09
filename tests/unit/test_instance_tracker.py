# -*- coding: utf-8 -*-
"""영상 · GIF 에서 고른 대상 따라가기 (services/instance_tracker · FrameRenderer).

두 사람(색이 다른 사각형)이 서로 지나가는 합성 영상 — "왼쪽 사람"은 처음 왼쪽이던 사람이어야 한다.
"""

from __future__ import annotations

import numpy as np

from app.schemas.request import InstanceSelector, ParsedPrompt
from app.services.instance_tracker import InstanceTracker, should_track
from app.services.segmentation import Instance, SegmentationResult
from app.services.video_processor import FrameRenderer

H, W, N = 120, 200, 20


def _clip(occlude_from: int | None = None, occlude_to: int | None = None):
    """(frames, A 마스크들, B 마스크들). A(빨강)는 왼→오, B(파랑)는 오→왼, 가운데서 지나간다. B 가 앞."""
    frames, ma, mb = [], [], []
    for t in range(N):
        xa = 10 + t * 8
        xb = 160 - t * 8
        a = np.zeros((H, W), bool)
        b = np.zeros((H, W), bool)
        a[30:110, xa: xa + 30] = True
        b[25:110, xb: xb + 30] = True
        a &= ~b
        if occlude_from is not None and occlude_from <= t < occlude_to:
            a[:] = False  # 완전히 가려진(검출 실패) 프레임
        frame = np.full((H, W, 3), 200, np.uint8)
        frame[a] = (40, 40, 220)
        frame[b] = (220, 60, 40)
        frames.append(frame)
        ma.append(a)
        mb.append(b)
    return frames, ma, mb


class _Seg:
    def __init__(self, ma, mb):
        self.it = iter(zip(ma, mb))
        self.flip = False

    def predict(self, frame, targets=None):
        items = [Instance.from_mask(m.astype(np.uint8) * 255, "person", 0.9) for m in next(self.it) if m.any()]
        self.flip = not self.flip
        if self.flip:
            items.reverse()  # 검출 순서는 매번 달라도 같은 대상을 따라가야 한다
        union = np.zeros((H, W), np.uint8)
        for i in items:
            union |= i.mask
        return SegmentationResult(mask=union, instances=items, labels=["person"] * len(items), backend="test")


def _overlaps(mask, target):
    return np.logical_and(mask > 127, target).sum() / max(1, target.sum())


def test_should_track_only_fixed_count_selectors():
    assert not should_track(None)
    assert not should_track(InstanceSelector())
    assert not should_track(InstanceSelector(attributes=["red shirt"]))  # 조건 맞는 전부 — 새로 들어온 사람도 포함해야 한다
    assert should_track(InstanceSelector(position="left"))
    assert should_track(InstanceSelector(count=2))
    assert should_track(InstanceSelector(rank=2))


def _renderer(ma, mb, track):
    parsed = ParsedPrompt(target=["person"], effect="remove_bg", selector=InstanceSelector(position="left"))
    return FrameRenderer(parsed, _Seg(ma, mb), smoothing="off", track=track)


def test_left_person_keeps_identity_after_crossing():
    frames, ma, mb = _clip()
    tracked = _renderer(ma, mb, True)
    per_frame = _renderer(ma, mb, False)
    for t, f in enumerate(frames):
        m_track = tracked.mask(f)
        m_frame = per_frame.mask(f)
        if t == N - 1:
            assert _overlaps(m_track, ma[t]) > 0.9 and _overlaps(m_track, mb[t]) < 0.1  # 처음 왼쪽이던 A 를 계속
            assert _overlaps(m_frame, mb[t]) > 0.9  # 프레임마다 다시 고르면 지금 왼쪽인 B 로 바뀐다
    assert tracked.tracker.reselected == 1


def test_reacquires_after_full_occlusion_without_switching():
    """대상이 몇 프레임 완전히 가려져도 다른 사람으로 옮겨 가지 않고(직전 마스크 유지) 다시 나타나면 이어서 따라간다."""
    frames, ma, mb = _clip(occlude_from=8, occlude_to=12)
    r = _renderer(ma, mb, True)
    for t, f in enumerate(frames):
        m = r.mask(f)
        if 8 <= t < 12:
            assert _overlaps(m, mb[t]) < 0.9  # 가려진 동안 B 를 대신 고르지 않는다 (직전 A 마스크를 B 가 지나가며 일부 겹칠 뿐)
        if t >= 13:
            assert _overlaps(m, ma[t]) > 0.9
    assert r.held >= 4 and r.tracker.reselected == 1


def test_reselects_when_lost_for_long():
    sel = InstanceSelector(position="left")
    tracker = InstanceTracker(sel)
    frame = np.full((H, W, 3), 128, np.uint8)
    left = np.zeros((H, W), np.uint8)
    left[10:50, 10:40] = 255
    right = np.zeros((H, W), np.uint8)
    right[10:50, 150:180] = 255
    a = Instance.from_mask(left, "person", 0.9)
    assert tracker.choose([a], frame) == [a]
    for _ in range(20):
        tracker.choose([], frame)
    b = Instance.from_mask(right, "person", 0.9)
    assert tracker.choose([b], frame) == [b]  # 오래 못 찾았으면 selector 로 다시
    assert tracker.reselected == 2
