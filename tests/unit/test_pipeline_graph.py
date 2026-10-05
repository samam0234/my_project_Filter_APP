# -*- coding: utf-8 -*-
"""LangGraph 파이프라인 동작 테스트 — 재시도 전략 · 최선 시도 채택 · 노드 시간 측정.

세그멘터·LLM 은 가짜로 바꿔 YOLO·Ollama 없이 그래프 흐름만 검증한다.
"""

from __future__ import annotations

import shutil

import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")
pytest.importorskip("pydantic_settings")

from app.core.config import get_settings
from app.services.segmentation import SegmentationResult
from app.workflows import graph, nodes

H, W = 60, 80


def _jpeg() -> bytes:
    ok, buf = cv2.imencode(".jpg", np.full((H, W, 3), 128, np.uint8))
    return buf.tobytes()


def _mask(kind: str):
    m = np.zeros((H, W), np.uint8)
    if kind == "good":
        m[15:45, 20:60] = 255  # 약 25% — 검증 통과
    elif kind == "tiny":
        m[0, 0] = 255  # 면적 너무 작음 → fallback
    return m  # "empty" → failed


class FakeSegmentor:
    def __init__(self, plan):
        self.plan = list(plan)
        self.calls = []

    def predict(self, image, targets=None, min_confidence=None):
        self.calls.append({"image": image, "min_confidence": min_confidence})
        kind, conf = self.plan[len(self.calls) - 1]
        mask = _mask(kind)
        return SegmentationResult(
            mask=mask,
            confidences=[conf] if mask.any() else [],
            labels=["person"] if mask.any() else [],
            backend="fake",
        )


class FakeProcessor:
    def __init__(self, plan):
        self.settings = get_settings()
        self.segmentor = FakeSegmentor(plan)

    def preprocess(self, image):
        return cv2.add(image, 20)  # CLAHE 대신 밝기만 바꿔 원본 축소본과 구분


@pytest.fixture()
def run(monkeypatch):
    made = []

    def _run(plan):
        proc = FakeProcessor(plan)
        monkeypatch.setattr(nodes, "_get_processor", lambda: proc)
        monkeypatch.setattr(nodes, "parse_prompt_llm", lambda prompt, settings, **kw: None)  # 키워드 파서
        result = graph.run_pipeline(_jpeg(), "사람만 남기고 배경 제거", job_id=f"zzgraph{len(made)}", persist=False)
        made.append(result.job_id)
        return result, proc

    yield _run
    for job_id in made:
        shutil.rmtree(get_settings().upload_path / job_id, ignore_errors=True)


def test_ok_on_first_try_has_no_retry_and_records_timings(run):
    result, proc = run([("good", 0.9)])
    assert result.status == "ok"
    assert len(proc.segmentor.calls) == 1
    assert proc.segmentor.calls[0]["min_confidence"] is None
    assert result.meta["attempts"] == 1
    assert result.meta["segment_strategy"] == "default"
    timings = result.meta["timings"]
    for node in ("prompt_analyzer", "preprocessor", "segmentor", "validator", "effect_applier"):
        assert node in timings and timings[node] >= 0


def test_retry_changes_image_and_confidence_and_keeps_better_attempt(run):
    result, proc = run([("tiny", 0.9), ("good", 0.9)])
    first, second = proc.segmentor.calls
    assert first["min_confidence"] is None
    assert second["min_confidence"] == pytest.approx(get_settings().min_confidence * nodes.RETRY_CONFIDENCE_SCALE)
    assert not np.array_equal(first["image"], second["image"])  # CLAHE 사본 → 원본 축소본
    assert result.status == "ok"
    assert result.meta["attempts"] == 2
    assert result.meta["chosen_attempt"] == 2
    assert result.meta["segment_strategy"] == "retry_no_clahe_lowconf"


def test_worse_retry_does_not_replace_first_attempt(run):
    # 1차: 신뢰도 낮아 fallback(마스크는 있음) / 2차: 빈 마스크 failed → 1차 채택
    result, proc = run([("good", 0.05), ("empty", 0.0)])
    assert len(proc.segmentor.calls) == 2
    assert result.meta["chosen_attempt"] == 1
    assert result.status == "fallback"
    assert result.meta["segment_strategy"] == "default"
    assert result.meta["timings"]["segmentor"] >= 0
