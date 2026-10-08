# -*- coding: utf-8 -*-
"""경계·영상 안정화 튜닝 — 정제 1번, 선형 확대, 부드러운 알파, 시간축 스무딩."""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from app.schemas.request import ParsedPrompt
from app.services import effects
from app.services.effects import apply_blur, apply_effects, feather_alpha, upscale_mask


def _scene(h=120, w=160):
    img = np.full((h, w, 3), 40, np.uint8)
    img[30:90, 50:110] = (220, 200, 180)  # 밝은 피사체
    mask = np.zeros((h, w), np.uint8)
    mask[30:90, 50:110] = 255
    return img, mask


def test_apply_effects_skips_refine_when_already_refined(monkeypatch):
    """노드가 정제한 마스크를 apply_effects 가 또 정제하지 않는다 (GrabCut 2번 → 경계가 깎이고 시간 2배)."""
    calls = []
    monkeypatch.setattr(effects, "refine_mask", lambda m, i=None: calls.append(1) or m)
    img, mask = _scene()
    apply_effects(img, mask, ParsedPrompt(effect="blur"), refine=False)
    assert calls == []
    apply_effects(img, mask, ParsedPrompt(effect="blur"))  # 기본값(영상 경로)은 한 번 정제
    assert calls == [1]


def test_effect_node_refines_once(monkeypatch):
    """파이프라인 effect_applier 경로 전체에서 GrabCut 정제는 한 번."""
    from app.workflows import nodes

    calls = []
    real = effects.refine_mask
    monkeypatch.setattr(effects, "refine_mask", lambda m, i=None: calls.append(1) or real(m, i))
    img, mask = _scene()
    job = "edge-once-test"
    nodes._IMAGE_CACHE[job] = {"original": img, "mask": mask}
    try:
        nodes.effect_applier({"job_id": job, "parsed_prompt": {"effect": "blur", "target": ["person"]}})
    finally:
        nodes._IMAGE_CACHE.pop(job, None)
    assert calls == [1]


def test_upscale_mask_has_smaller_staircase():
    """줄여 세그한 마스크를 키울 때 최근접보다 선형+임계가 계단이 적다 (윤곽 길이가 실제 사선에 가깝다)."""
    small = np.zeros((40, 40), np.uint8)
    cv2.fillPoly(small, [np.array([[2, 38], [38, 2], [38, 38]])], 255)  # 사선 경계
    near = cv2.resize(small, (160, 160), interpolation=cv2.INTER_NEAREST)
    lin = upscale_mask(small, (160, 160))

    def perimeter(m):
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return sum(cv2.arcLength(c, True) for c in cs)

    assert perimeter(lin) < perimeter(near)
    assert set(np.unique(lin)) <= {0, 255}
    assert upscale_mask(small, (40, 40)) is not small  # 같은 크기면 복사본


def test_feather_alpha_softens_only_the_edge():
    img, mask = _scene()
    alpha = feather_alpha(mask, img)
    assert alpha[60, 80] == 255 and alpha[5, 5] == 0  # 안쪽·바깥은 그대로 (구멍·배경 새는 것 없음)
    edge = alpha[25:35, 45:115]
    assert ((edge > 0) & (edge < 255)).any()  # 경계에는 중간값
    assert feather_alpha(np.zeros_like(mask), img).max() == 0


def test_blur_blends_with_soft_alpha():
    img, mask = _scene()
    hard = apply_blur(img, mask, intensity=15)
    soft = apply_blur(img, feather_alpha(mask, img), intensity=15)
    assert (hard[60, 80] == img[60, 80]).all() and (soft[60, 80] == img[60, 80]).all()  # 피사체 선명
    # 경계 바로 바깥: 딱 자른 것보다 부드러운 쪽이 피사체 색과 배경 블러 사이로 이어진다
    jump = lambda out: np.abs(np.diff(out[60, 40:60].astype(int), axis=0)).max()  # noqa: E731
    assert jump(soft) <= jump(hard)


def test_remove_bg_alpha_is_soft_at_edge():
    img, mask = _scene()
    out = apply_effects(img, mask, ParsedPrompt(effect="remove_bg"), refine=False)
    a = out[:, :, 3]
    assert a[60, 80] == 255 and a[5, 5] == 0
    assert ((a > 0) & (a < 255)).any()


# --------------------------------------------------------------------------- 영상


def _moving(frames=10, step=4, h=96, w=160):
    seq = []
    for t in range(frames):
        img = np.full((h, w, 3), 30, np.uint8)
        x = 20 + t * step
        img[30:70, x : x + 40] = (230, 210, 190)
        m = np.zeros((h, w), np.uint8)
        m[30:70, x : x + 40] = 255
        seq.append((img, m))
    return seq


def _iou(a, b):
    a, b = a > 127, b > 127
    return np.logical_and(a, b).sum() / max(np.logical_or(a, b).sum(), 1)


def test_smoother_ignores_single_frame_dropout():
    """한 프레임만 세그가 빠져도(사람이 잠깐 사라짐) 마스크가 깜빡이지 않는다."""
    from app.services.video_processor import TemporalSmoother

    img, mask = _moving(1)[0]
    s = TemporalSmoother("flow", 0.3)
    s.update(img, mask)
    s.update(img, mask)
    out = s.update(img, np.zeros_like(mask))  # 이번 프레임만 놓침
    assert _iou(out, mask) > 0.9


def test_flow_smoother_follows_motion_without_tail():
    """움직이는 대상: 흐름 보정은 현재 위치를 따라가고, 그냥 섞기(ema)는 지나간 자리에 꼬리가 남는다."""
    from app.services.video_processor import TemporalSmoother

    seq = _moving()
    flow, ema = TemporalSmoother("flow", 0.3), TemporalSmoother("ema", 0.3)
    f_iou, e_iou = [], []
    for img, m in seq:
        f_iou.append(_iou(flow.update(img, m), m))
        e_iou.append(_iou(ema.update(img, m), m))
    assert np.mean(f_iou[2:]) > 0.9
    assert np.mean(f_iou[2:]) > np.mean(e_iou[2:])


def test_smoother_resets_on_scene_cut():
    from app.services.video_processor import TemporalSmoother

    a_img, a_mask = _moving(1)[0]
    b_img = np.full_like(a_img, 230)  # 완전히 다른 장면
    s = TemporalSmoother("flow", 0.3)
    s.update(a_img, a_mask)
    assert not s.update(b_img, np.zeros_like(a_mask)).any()  # 이전 장면 마스크가 남지 않음


def test_smoothing_weight_must_be_below_half():
    """이진 마스크라 현재 프레임 비중이 0.5 이상이면 스무딩이 아무 일도 안 한다 — 설정에서 막는다."""
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings.model_validate({"DB_DIALECT": "sqlite", "VIDEO_SMOOTHING_WEIGHT": 0.6})
    assert Settings.model_validate({"DB_DIALECT": "sqlite"}).video_temporal_smoothing == "flow"
