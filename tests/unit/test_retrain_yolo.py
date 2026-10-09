# -*- coding: utf-8 -*-
"""YOLO 재학습 루프(scripts/retrain_yolo.py) — 어려운 사례 판별과 채택 판정. 학습 없이 검증한다."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


retrain_yolo = _load("retrain_yolo", REPO_ROOT / "scripts/retrain_yolo.py")


def _s(pick, leak5):
    return {"n": 40, "pick_ok": pick, "leak": 0.03, "leak_case5": leak5, "iou": 0.8, "cover": 0.9}


def test_yolo_decide_requires_hard_gain_without_regressions():
    base = {s: _s(0.90, 0.20) for s in retrain_yolo.SCENARIOS}
    better = {**base, "touching": _s(0.92, 0.12)}
    assert retrain_yolo.decide(better, base, 0.40, 0.40)[0]
    assert not retrain_yolo.decide(better, base, 0.39, 0.40)[0]  # 일반 성능 0.5%p 넘게 하락
    worse_elsewhere = {**better, "dog": _s(0.90, 0.30)}
    assert not retrain_yolo.decide(worse_elsewhere, base, 0.40, 0.40)[0]
    assert not retrain_yolo.decide(dict(base), base, 0.40, 0.40)[0]  # 좋아진 것 없음


def test_yolo_hard_case_detects_touching_instances():
    w, h = 640, 480
    a = {"area": 0.1 * w * h, "bbox": [100, 100, 150, 300]}
    near = {"area": 0.1 * w * h, "bbox": [255, 100, 150, 300]}  # 5px 떨어짐 → 맞닿은 것으로
    far = {"area": 0.1 * w * h, "bbox": [480, 100, 150, 300]}
    tiny = {"area": 10, "bbox": [240, 100, 5, 5]}
    assert retrain_yolo._is_hard([a, near], w, h)
    assert not retrain_yolo._is_hard([a, far], w, h)
    assert not retrain_yolo._is_hard([a, tiny], w, h)
