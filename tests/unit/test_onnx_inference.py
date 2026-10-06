# -*- coding: utf-8 -*-
"""직접 구현한 ONNX 세그 추론 (onnx_utils) — 모델 파일 없이 합성 출력으로 검증.

실제 모델과의 일치는 scripts/experiments/onnx_vs_pt.py (docs/plan/ONNX_INFERENCE.md).
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")
pytest.importorskip("loguru")

from app.utils.onnx_utils import (
    class_names,
    input_size,
    letterbox,
    postprocess,
    preprocess,
    run_yolo_seg_onnx,
)

S = 640
NM = 32


def _output(boxes, nc=3, mh=160):
    """boxes: [(cx, cy, w, h, cls, conf, 마스크 로짓 사각형 (x0,y0,x1,y1) proto 좌표)] → (output0, output1)."""
    a = len(boxes)
    out0 = np.zeros((1, 4 + nc + NM, max(a, 1)), np.float32)
    proto = np.full((1, NM, mh, mh), -10.0, np.float32)  # 채널 0 이 마스크, 나머지는 0 계수
    proto[0, 1:] = 0.0
    for i, (cx, cy, w, h, c, conf, rect) in enumerate(boxes):
        out0[0, :4, i] = (cx, cy, w, h)
        out0[0, 4 + c, i] = conf
        out0[0, 4 + nc, i] = 1.0  # 마스크 계수: 채널 0 만
        x0, y0, x1, y1 = rect
        proto[0, 0, y0:y1, x0:x1] = 10.0
    return out0, proto


class _Meta:
    def __init__(self, names):
        self.custom_metadata_map = {"names": names} if names is not None else {}


class _Input:
    name = "images"

    def __init__(self, shape):
        self.shape = shape


class FakeSession:
    def __init__(self, boxes, shape=(1, 3, S, S), names="{0: 'person', 1: 'dog', 2: 'cat'}"):
        self._out = _output(boxes)
        self._shape = list(shape)
        self._names = names
        self.fed = None

    def get_inputs(self):
        return [_Input(self._shape)]

    def run(self, _outputs, feed):
        self.fed = feed["images"]
        return list(self._out)

    def get_modelmeta(self):
        return _Meta(self._names)


def test_letterbox_centers_with_gray_padding():
    img = np.full((100, 200, 3), 50, np.uint8)  # 2:1
    boxed, r, (top, left) = letterbox(img, (S, S))
    assert boxed.shape == (S, S, 3) and r == pytest.approx(3.2)
    assert (top, left) == (round((S - 320) / 2 - 0.1), 0)
    assert boxed[0, 0].tolist() == [114, 114, 114]  # 패딩
    assert boxed[S // 2, S // 2].tolist() == [50, 50, 50]  # 이미지


def test_preprocess_is_nchw_rgb_unit_range():
    img = np.zeros((S, S, 3), np.uint8)
    img[..., 0] = 255  # BGR 의 B
    blob, r, pad = preprocess(img, (S, S))
    assert blob.shape == (1, 3, S, S) and blob.dtype == np.float32
    assert blob[0, 2].max() == 1.0 and blob[0, 0].max() == 0.0  # B 는 RGB 의 마지막 채널
    assert r == 1.0 and pad == (0, 0)


def test_input_size_falls_back_for_dynamic_axes():
    assert input_size(FakeSession([], shape=(1, 3, 480, 640))) == (480, 640)
    assert input_size(FakeSession([], shape=(1, 3, "height", "width"))) == (640, 640)


def test_postprocess_filters_confidence_and_restores_original_coordinates():
    # 640x640 입력에 정사각 이미지(1280x1280, 배율 0.5): person 은 입력 (100..300, 200..400) 영역
    boxes = [
        (200, 300, 200, 200, 0, 0.9, (25, 50, 75, 100)),  # person, proto 격자 = 입력/4
        (500, 500, 100, 100, 1, 0.1, (110, 110, 140, 140)),  # 신뢰도 낮음 → 제외
    ]
    out0, proto = _output(boxes)
    res = postprocess([out0, proto], (1280, 1280), 0.5, (0, 0), (S, S), 0.25)
    assert len(res) == 1
    cls, conf, mask = res[0]
    assert (cls, round(conf, 2)) == (0, 0.9) and mask.shape == (1280, 1280) and mask.dtype == np.uint8
    ys, xs = np.nonzero(mask)
    # 입력 (100..300, 200..400) → 원본 (200..600, 400..800)
    assert abs(xs.min() - 200) <= 4 and abs(xs.max() - 600) <= 4
    assert abs(ys.min() - 400) <= 4 and abs(ys.max() - 800) <= 4
    assert set(np.unique(mask)) <= {0, 255}


def test_postprocess_removes_letterbox_padding_offset():
    # 2:1 이미지(200x100)를 640 입력에 넣으면 위아래 160px 패딩. 입력의 (0..640, 160..480) 이 이미지 전체
    img_h, img_w = 100, 200
    r, top = 3.2, round((S - 320) / 2 - 0.1)
    out0, proto = _output([(320, 320, 640, 320, 2, 0.8, (0, 40, 160, 120))])  # 이미지 전체 영역
    res = postprocess([out0, proto], (img_h, img_w), r, (top, 0), (S, S), 0.25)
    assert len(res) == 1
    mask = res[0][2]
    assert mask.shape == (img_h, img_w)
    assert mask.mean() / 255 > 0.95  # 패딩이 아니라 이미지 전체가 마스크


def test_nms_removes_duplicates_per_class_only():
    same = [(200, 200, 100, 100, 0, 0.9, (40, 40, 60, 60)), (202, 202, 100, 100, 0, 0.8, (40, 40, 60, 60))]
    other_class = [(200, 200, 100, 100, 1, 0.7, (40, 40, 60, 60))]
    out0, proto = _output(same + other_class)
    res = postprocess([out0, proto], (S, S), 1.0, (0, 0), (S, S), 0.25)
    assert sorted(c for c, _, _ in res) == [0, 1]  # 같은 클래스 겹침은 하나만, 다른 클래스는 둘 다


def test_run_yolo_seg_onnx_end_to_end_with_fake_session():
    sess = FakeSession([(320, 320, 200, 200, 1, 0.95, (60, 60, 100, 100))])
    img = np.zeros((480, 640, 3), np.uint8)
    res = run_yolo_seg_onnx(sess, img, 0.25)
    assert sess.fed.shape == (1, 3, S, S)
    assert len(res) == 1 and res[0][0] == 1 and res[0][2].shape == (480, 640)


def test_class_names_from_metadata():
    assert class_names(FakeSession([])) == {0: "person", 1: "dog", 2: "cat"}
    assert class_names(FakeSession([], names=None)) == {}
    assert class_names(FakeSession([], names="{not python")) == {}  # 깨져도 추론은 가능


def _onnx_segmentor(boxes, min_conf=0.25):
    import threading

    from app.core.config import Settings
    from app.services.segmentation import Segmentor

    seg = Segmentor.__new__(Segmentor)
    seg.settings = Settings.model_validate({"DB_DIALECT": "sqlite", "MIN_CONFIDENCE": min_conf})
    seg._yolo = None
    seg._session = FakeSession(boxes)
    seg._onnx_names = None
    seg._ready = True
    seg._lock = threading.Lock()
    return seg


def test_segmentor_onnx_path_filters_requested_labels():
    seg = _onnx_segmentor([
        (200, 200, 120, 120, 0, 0.9, (30, 30, 70, 70)),  # person
        (480, 480, 120, 120, 1, 0.8, (100, 100, 140, 140)),  # dog
    ])
    res = seg.predict(np.zeros((S, S, 3), np.uint8), targets=["person"])
    assert res.backend == "onnx" and res.labels == ["person"] and res.mask.any()
    assert sorted(res.detected) == ["dog", "person"]  # 필터 전 감지 목록은 그대로 (대상 못 찾음 안내용)
    assert len(res.instances) == 1 and res.instances[0].label == "person"


def test_segmentor_onnx_min_confidence_override():
    seg = _onnx_segmentor([(200, 200, 120, 120, 0, 0.2, (30, 30, 70, 70))])
    img = np.zeros((S, S, 3), np.uint8)
    assert not seg.predict(img, targets=["person"]).mask.any()  # 기본 0.25 에 걸림
    assert seg.predict(img, targets=["person"], min_confidence=0.1).labels == ["person"]  # 재시도 기준


def test_segmentor_onnx_no_target_returns_empty_mask_not_stub():
    seg = _onnx_segmentor([(480, 480, 120, 120, 1, 0.8, (100, 100, 140, 140))])
    res = seg.predict(np.zeros((S, S, 3), np.uint8), targets=["person"])
    assert res.backend == "onnx" and not res.mask.any() and res.detected == ["dog"]
