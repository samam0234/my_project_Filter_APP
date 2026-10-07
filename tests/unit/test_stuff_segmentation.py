# -*- coding: utf-8 -*-
"""배경 덩어리(건물·하늘·도로…) 세그 — 어휘 정규화, 묶음 확률, Segmentor 연결, 모델이 있을 때의 실제 추론."""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from app.core.config import Settings
from app.services.prompt_spec import STUFF_CLASSES, STUFF_GROUPS, canonical_target, normalize_parsed
from app.services.segmentation import Segmentor
from app.services.stuff_segmentation import (
    StuffSegmenter,
    group_ids,
    group_probability,
    preprocess,
    split_components,
)

ID2LABEL = {0: "wall", 1: "building", 2: "sky", 3: "floor", 4: "tree", 25: "house", 48: "skyscraper", 79: "hovel", 6: "road"}


def _settings(**v) -> Settings:
    return Settings.model_validate({"DB_DIALECT": "sqlite", "PRELOAD_MODELS": False, **v})


# --------------------------------------------------------------------------- 어휘


@pytest.mark.parametrize(
    "word, expected",
    [("건물", "building"), ("빌딩", "building"), ("buildings", "building"), ("house", "building"), ("아파트", "building"),
     ("하늘", "sky"), ("도로", "road"), ("나무", "tree"), ("trees", "tree"), ("잔디", "grass"), ("바다", "water"),
     ("lake", "water"), ("벽", "wall"), ("building", "building"), ("sky", "sky")],
)
def test_stuff_words_become_canonical_targets(word, expected):
    assert canonical_target(word) == expected


def test_coco_targets_are_untouched():
    for name in ("person", "car", "dog", "chair", "potted plant"):
        assert canonical_target(name) == name and name not in STUFF_CLASSES


def test_stuff_names_never_collide_with_coco():
    from app.services.prompt_spec import COCO_CLASSES

    assert not (STUFF_CLASSES & COCO_CLASSES)


def test_llm_json_with_building_target_is_kept():
    parsed = normalize_parsed({"target": ["건물"], "effect": "keep", "intensity": 15})
    assert parsed.target == ["building"] and parsed.effect == "remove_bg"


def test_heuristic_parser_understands_scenery():
    from app.workflows.nodes import parse_prompt_heuristic

    assert parse_prompt_heuristic("건물만 남기고 배경 제거").target == ["building"]
    assert parse_prompt_heuristic("하늘 빼고 전부 블러").target == ["sky"]
    assert parse_prompt_heuristic("사람이랑 건물만 남겨").target == ["person", "building"]
    assert parse_prompt_heuristic("배경 블러").target == ["person"]  # 대상이 없으면 예전처럼 사람


def test_every_group_maps_to_real_ade_labels(tmp_path):
    """묶음이 가리키는 이름이 ADE20K 라벨에 실제로 있다 (오타로 빈 묶음이 되지 않게)."""
    import json
    from glob import glob
    from pathlib import Path

    found = glob(str(Path.home() / ".cache/huggingface/hub/models--nvidia--segformer-b0-finetuned-ade-512-512/snapshots/*/config.json"))
    if not found:
        pytest.skip("SegFormer config 캐시 없음")
    id2label = {int(k): v for k, v in json.loads(Path(found[0]).read_text(encoding="utf-8"))["id2label"].items()}
    for group in STUFF_GROUPS:
        assert group_ids(id2label, group), group
    assert len(group_ids(id2label, "building")) == 4  # building, house, skyscraper, hovel


# --------------------------------------------------------------------------- 묶음 확률


def test_group_ids_use_all_members():
    assert group_ids(ID2LABEL, "building") == [1, 25, 48, 79]
    assert group_ids(ID2LABEL, "sky") == [2]


def test_group_probability_sums_member_classes():
    """픽셀이 'building 0.3 + house 0.3 + skyscraper 0.2' 면 개별로는 sky 에 질 수 있어도 묶음으로는 건물 (0.8)."""
    c, h, w = 150, 4, 4
    logits = np.full((c, h, w), -10.0, np.float32)
    logits[1] = np.log(0.3)
    logits[25] = np.log(0.3)
    logits[48] = np.log(0.2)
    logits[2] = np.log(0.35)  # sky 가 단일 클래스로는 1등
    prob = group_probability(logits, group_ids(ID2LABEL, "building"), (8, 8))
    assert prob.shape == (8, 8) and prob.min() > 0.5
    assert group_probability(logits, [2], (8, 8)).max() < 0.5


def test_preprocess_shape_and_range():
    x = preprocess(np.full((30, 50, 3), 255, np.uint8), 64)
    assert x.shape == (1, 3, 64, 64) and x.dtype == np.float32
    assert abs(x[0, 0, 0, 0] - (1 - 0.485) / 0.229) < 1e-4


def test_split_components_orders_by_size_and_drops_specks():
    mask = np.zeros((100, 100), np.uint8)
    mask[10:60, 10:60] = 255  # 큰 건물
    mask[70:80, 70:80] = 255  # 작은 건물 (면적 1%)
    mask[95, 95] = 255  # 1픽셀 점 — 인스턴스로는 버림
    comps = split_components(mask, np.full((100, 100), 0.9, np.float32), "building")
    assert [c[3] for c in comps] == [(10, 10, 60, 60), (70, 70, 80, 80)]
    assert all(abs(c[2] - 0.9) < 1e-6 for c in comps)


# --------------------------------------------------------------------------- Segmentor 연결


class _FakeStuff:
    available = True

    def __init__(self):
        self.calls = []

    def predict(self, image, groups):
        self.calls.append(list(groups))
        h, w = image.shape[:2]
        m = np.zeros((h, w), np.uint8)
        m[: h // 2] = 255
        return m, [(m.copy(), groups[0], 0.9, (0, 0, w, h // 2))]


def _segmentor(**v):
    seg = Segmentor(_settings(YOLO_MODEL_PATH="models/missing-stuff.pt", **v))
    seg._stuff = _FakeStuff()
    return seg


def test_stuff_target_goes_to_segformer_not_yolo():
    seg = _segmentor()
    res = seg.predict(np.zeros((40, 60, 3), np.uint8), targets=["building"])
    assert res.backend == "segformer" and res.labels == ["building"] and res.detected == ["building"]
    assert res.mask[:20].all() and not res.mask[20:].any()
    assert seg._stuff.calls == [["building"]]


def test_mixed_targets_union_both_paths():
    seg = _segmentor()
    img = np.zeros((40, 60, 3), np.uint8)
    base = np.zeros((40, 60), np.uint8)
    base[30:, :] = 255

    from app.services.segmentation import SegmentationResult

    seg_calls = []

    def fake_base(image, targets, min_confidence=None):
        seg_calls.append(list(targets))
        return SegmentationResult(mask=base, confidences=[0.8], labels=["person"], backend="yolo", detected=["person"])

    seg_orig = seg.predict
    seg.predict = lambda image, targets=None, min_confidence=None: (
        fake_base(image, targets, min_confidence) if targets == ["person"] else seg_orig(image, targets, min_confidence)
    )
    res = seg.predict(img, targets=["person", "building"])
    assert seg_calls == [["person"]] and seg._stuff.calls == [["building"]]
    assert res.backend == "yolo+segformer" and res.labels == ["person", "building"]
    assert res.mask[:20].all() and res.mask[30:].all() and not res.mask[20:30].any()


def test_without_model_file_falls_back_to_old_flow(tmp_path):
    seg = Segmentor(_settings(YOLO_MODEL_PATH="models/missing-stuff.pt", STUFF_MODEL_PATH=str(tmp_path / "none.onnx")))
    assert not seg.stuff_segmenter().available
    res = seg.predict(np.zeros((40, 60, 3), np.uint8), targets=["building"])
    assert res.backend != "segformer"  # 예전처럼 stub/빈 결과 — 서비스가 죽지 않는다


def test_disabled_flag_skips_stuff(tmp_path):
    assert not StuffSegmenter(_settings(STUFF_SEG_ENABLED=False)).available


# --------------------------------------------------------------------------- 실제 모델 (파일이 있을 때만)


@pytest.fixture(scope="module")
def real_stuff():
    settings = _settings()
    if not settings.stuff_model_file.is_file():
        pytest.skip("segformer-ade.onnx 없음 (scripts/export_stuff_onnx.py)")
    seg = StuffSegmenter(settings)
    if not seg.available:
        pytest.skip("모델을 열 수 없음")
    return seg


def test_real_model_finds_sky_and_building_in_synthetic_street(real_stuff):
    """윗부분 하늘색 · 아랫부분 회색 건물 모양 — 완벽할 필요 없이 위는 하늘이 우세하고 방향이 맞는지만."""
    img = np.zeros((384, 512, 3), np.uint8)
    img[:150] = (235, 206, 135)  # 하늘색 (BGR)
    img[150:] = (120, 120, 130)
    mask, comps = real_stuff.predict(img, ["sky"])
    assert mask.shape == img.shape[:2]
    assert mask[:100].mean() > mask[300:].mean()
    assert all(c[1] == "sky" for c in comps)
