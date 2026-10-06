# -*- coding: utf-8 -*-
"""YOLO 대상 필터 테스트 (가짜 YOLO, ultralytics 불필요).

요청한 target 라벨만 마스크에 합치는지, 대상이 없으면 stub 대신
빈 마스크를 돌려주는지 확인한다.
"""

from __future__ import annotations

import threading

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
    """Ultralytics 처럼 conf 미만 검출은 predict 단계에서 버린다 (기본 0.25)."""

    def __init__(self, result):
        self._result = result
        self.calls: list[float] = []
        self.retina = None

    def predict(self, img, verbose=False, conf=0.25, retina_masks=False):
        self.calls.append(conf)
        self.retina = retina_masks
        r = self._result
        keep = [i for i, c in enumerate(r.boxes.conf) if c.item() >= conf]
        if r.masks is None or len(keep) == len(r.boxes.conf):
            return [r]
        out = _Result.__new__(_Result)
        out.names = r.names
        data = r.masks.data.cpu().numpy()[keep] if keep else None
        out.masks = type("M", (), {"data": _Tensor(data)})() if keep else None
        out.boxes = _Boxes([r.boxes.cls[i].item() for i in keep], [r.boxes.conf[i].item() for i in keep])
        return [out]


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
    seg._lock = threading.Lock()
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


def test_coco_bag_alias_matches_custom_model_label():
    """LLM 이 handbag 이라고 해도 커스텀 모델의 bag 을 잡는다 (양방향 별칭)."""
    from app.services.segmentation import expand_targets

    assert "bag" in expand_targets({"handbag"})
    assert "backpack" in expand_targets({"bag"})
    seg = _segmentor([(3, 0.8, (10, 20))])
    seg._yolo = _FakeYolo(_Result([(3, 0.8, (10, 20))], {3: "bag"}))
    r = seg.predict(np.zeros((H, W, 3), np.uint8), targets=["handbag"])
    assert r.labels == ["bag"]


def test_create_session_skips_non_onnx(tmp_path):
    """.pt 를 ONNX 로 열지 않는다 (Ultralytics 로드 실패 시 파이프라인이 멈추던 문제)."""
    from app.utils.onnx_utils import create_session

    fake_pt = tmp_path / "yolo.pt"
    fake_pt.write_bytes(b"not onnx")
    assert create_session(fake_pt) is None
    broken = tmp_path / "broken.onnx"
    broken.write_bytes(b"not a protobuf")
    assert create_session(broken) is None


def test_min_confidence_override_includes_low_confidence_target():
    """재시도용 신뢰도 기준 완화 — 기본 기준에서 빠지던 낮은 신뢰도 대상이 포함된다."""
    img = np.zeros((H, W, 3), np.uint8)
    default = _segmentor().predict(img, targets=["person"])
    seg = _segmentor()
    relaxed = seg.predict(img, targets=["person"], min_confidence=0.05)
    assert len(relaxed.labels) == len(default.labels) + 1
    # 낮춘 기준이 모델 predict 까지 전달돼야 한다 (안 넘기면 Ultralytics 기본 0.25 가 먼저 거름)
    assert seg._yolo.calls[-1] == 0.05


def test_yolo_predict_uses_full_resolution_masks():
    seg = _segmentor()
    seg.predict(np.zeros((H, W, 3), np.uint8), targets=["person"])
    assert seg._yolo.retina is True  # 기본 letterbox 크기 마스크를 단순 확대하면 경계가 거칠어진다
