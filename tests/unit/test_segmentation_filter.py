# -*- coding: utf-8 -*-
"""YOLO 대상 필터 테스트 (가짜 YOLO, ultralytics 불필요).

요청한 target 라벨만 마스크에 합치는지, 대상이 없으면 stub 대신
빈 마스크를 돌려주는지 확인한다.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("cv2")
pytest.importorskip("pydantic_settings")

from app.core.config import Settings
from app.services.segmentation import Segmentor

H, W = 40, 60


class _Scalar:
    def __init__(self, v):
        self._v = v

    def item(self):
        return self._v


class _Tensor:
    """masks.data.cpu().numpy() 체인 흉내."""

    def __init__(self, arr):
        self._arr = arr

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class _Boxes:
    def __init__(self, cls_ids, confs):
        self.cls = [_Scalar(c) for c in cls_ids]
        self.conf = [_Scalar(c) for c in confs]


class _Result:
    def __init__(self, instances, names):
        # instances: [(cls_id, conf, (x0, x1)), ...] — x 구간을 1 로 채운 마스크
        masks = []
        for _, _, (x0, x1) in instances:
            m = np.zeros((H, W), dtype=np.float32)
            m[:, x0:x1] = 1.0
            masks.append(m)
        self.names = names
        self.masks = type("M", (), {"data": _Tensor(np.stack(masks))})() if masks else None
        self.boxes = _Boxes([i[0] for i in instances], [i[1] for i in instances])


class _FakeYolo:
    def __init__(self, result):
        self._result = result

    def predict(self, img, verbose=False):
        return [self._result]


NAMES = {0: "person", 1: "car", 2: "dog"}
# person(0~10) · car(20~30, 높은 conf) · person 저신뢰(40~50) · dog(50~60)
SCENE = [
    (0, 0.90, (0, 10)),
    (1, 0.77, (20, 30)),
    (0, 0.10, (40, 50)),
    (2, 0.60, (50, 60)),
]


def _segmentor(instances=SCENE) -> Segmentor:
    seg = Segmentor.__new__(Segmentor)  # 가중치 로드 생략
    seg.settings = Settings.model_validate({"DB_DIALECT": "sqlite"})
    seg._session = None
    seg._yolo = _FakeYolo(_Result(instances, NAMES))
    seg._ready = True
    return seg


def _cols(mask) -> set[int]:
    return set(np.where(mask.any(axis=0))[0].tolist())


def test_only_requested_label_kept():
    """person 요청 시 신뢰도 높은 car 는 섞이지 않는다 (기존 버그)."""
    r = _segmentor().predict(np.zeros((H, W, 3), np.uint8), targets=["person"])
    assert r.labels == ["person"]
    assert _cols(r.mask) == set(range(0, 10))
    assert r.backend == "yolo"


def test_low_confidence_target_excluded():
    """대상 라벨이어도 min_confidence 미만이면 제외."""
    r = _segmentor().predict(np.zeros((H, W, 3), np.uint8), targets=["person"])
    assert not (_cols(r.mask) & set(range(40, 50)))


def test_multiple_targets_union():
    r = _segmentor().predict(np.zeros((H, W, 3), np.uint8), targets=["person", "dog"])
    assert sorted(r.labels) == ["dog", "person"]
    assert _cols(r.mask) == set(range(0, 10)) | set(range(50, 60))


def test_all_keeps_every_confident_instance():
    r = _segmentor().predict(np.zeros((H, W, 3), np.uint8), targets=["all"])
    assert sorted(r.labels) == ["car", "dog", "person"]


def test_missing_target_returns_empty_mask_not_stub():
    """대상이 없으면 가짜 타원(stub) 대신 빈 마스크 + 감지 목록."""
    r = _segmentor().predict(np.zeros((H, W, 3), np.uint8), targets=["bus"])
    assert r.backend == "yolo"
    assert not r.mask.any()
    assert r.labels == []
    assert sorted(set(r.detected)) == ["car", "dog", "person"]


def test_validator_node_explains_missing_target():
    nodes = pytest.importorskip("app.workflows.nodes")
    nodes._IMAGE_CACHE["t1"] = {"mask": np.zeros((H, W), np.uint8)}
    try:
        out = nodes.validator_node(
            {
                "job_id": "t1",
                "parsed_prompt": {"target": ["bus"]},
                "detected": ["person", "car", "person"],
                "confidences": [],
            }
        )
    finally:
        nodes.clear_job_cache("t1")
    assert out["status"] == "failed"
    assert "bus" in out["message"] and "car, person" in out["message"]
