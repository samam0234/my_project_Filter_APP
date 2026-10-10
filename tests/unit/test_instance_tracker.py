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


def _box(x0, x1, y0=10, y1=50):
    m = np.zeros((H, W), np.uint8)
    m[y0:y1, x0:x1] = 255
    return m


def test_reselects_when_lost_for_long():
    """오래 못 찾았고, 새로 보인 사람이 색도 다르면 selector 로 다시 고른다."""
    tracker = InstanceTracker(InstanceSelector(position="left"))
    frame = np.full((H, W, 3), 128, np.uint8)
    frame[10:50, 10:40] = (40, 40, 220)  # 처음 고른 사람: 빨강
    frame[10:50, 150:180] = (220, 60, 40)  # 나중에 보인 사람: 파랑
    a = Instance.from_mask(_box(10, 40), "person", 0.9)
    assert tracker.choose([a], frame) == [a]
    for _ in range(30):
        tracker.choose([], frame)
    b = Instance.from_mask(_box(150, 180), "person", 0.9)
    assert tracker.choose([b], frame) == [b]  # 색이 다른 새 사람 — 아는 사람이 아니므로 selector 로 이어 간다
    assert tracker.reidentified == 0 and tracker.reacquired == 1


def test_long_loss_does_not_jump_to_known_other_person():
    """오래 가려져도, 이미 따라가는 다른 사람(selector 기준으로는 지금 '왼쪽')으로 넘어가지 않는다."""
    tracker = InstanceTracker(InstanceSelector(position="left"))
    frame = np.full((H, W, 3), 128, np.uint8)
    frame[10:50, 10:40] = (40, 40, 220)
    frame[60:100, 150:180] = (220, 60, 40)
    a = Instance.from_mask(_box(10, 40), "person", 0.9)
    other = Instance.from_mask(_box(150, 180, 60, 100), "person", 0.9)
    assert tracker.choose([a, other], frame) == [a]
    for k in range(12):  # 고른 사람은 사라지고, 다른 사람은 왼쪽으로 걸어온다
        x = 150 - k * 10
        f = np.full((H, W, 3), 128, np.uint8)
        f[60:100, x:x + 30] = (220, 60, 40)
        assert tracker.choose([Instance.from_mask(_box(x, x + 30, 60, 100), "person", 0.9)], f) == []
    assert tracker.reacquired == 0 and tracker.reselected == 1


def test_reidentifies_same_looking_person_after_long_loss():
    """오래 가려졌다 엉뚱한 곳에서 다시 나타나도, 색이 같으면 selector(왼쪽) 대신 그 사람으로 이어 간다."""
    tracker = InstanceTracker(InstanceSelector(position="left"))
    frame = np.full((H, W, 3), 128, np.uint8)
    frame[10:50, 10:40] = (40, 40, 220)  # 고른 사람: 빨강 (왼쪽)
    frame[60:100, 60:90] = (220, 60, 40)  # 다른 사람: 파랑
    a = Instance.from_mask(_box(10, 40), "person", 0.9)
    other = Instance.from_mask(_box(60, 90, 60, 100), "person", 0.9)
    assert tracker.choose([a, other], frame) == [a]
    for _ in range(12):
        tracker.choose([other], frame)  # 고른 사람이 오래 안 보인다
    frame2 = np.full((H, W, 3), 128, np.uint8)
    frame2[10:50, 150:180] = (40, 40, 220)  # 빨간 사람이 오른쪽 끝에서 다시
    frame2[60:100, 20:50] = (220, 60, 40)  # 파란 사람은 이제 왼쪽
    back = Instance.from_mask(_box(150, 180), "person", 0.9)
    other2 = Instance.from_mask(_box(20, 50, 60, 100), "person", 0.9)
    assert tracker.choose([other2, back], frame2) == [back]
    assert tracker.reidentified == 1 and tracker.reselected == 1


def test_duplicate_detection_of_target_is_not_tracked_as_other_person():
    """한 사람이 겹친 마스크 두 개로 검출돼도, 다음 프레임에 하나만 나오면 그게 고른 대상이다."""
    tracker = InstanceTracker(InstanceSelector(position="left"))
    frame = np.full((H, W, 3), 128, np.uint8)
    frame[10:50, 10:40] = (40, 40, 220)
    frame[10:50, 150:180] = (220, 60, 40)
    part = Instance.from_mask(_box(10, 40, 10, 35), "person", 0.6)  # 같은 사람의 윗부분만
    whole = Instance.from_mask(_box(10, 40), "person", 0.9)
    right = Instance.from_mask(_box(150, 180), "person", 0.9)
    first = tracker.choose([part, whole, right], frame)
    assert len(first) == 1 and first[0] in (part, whole)
    assert sum(1 for t in tracker.tracks if not t.target) == 1  # 중복은 따로 추적하지 않는다 (오른쪽 사람만)
    again = Instance.from_mask(_box(12, 42), "person", 0.9)
    assert tracker.choose([again, right], frame) == [again]
