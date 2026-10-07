# -*- coding: utf-8 -*-
"""Phase 2: 배치 진행률, 영상 마스크 유지, 오픈보캐브 폴백, LoRA 템플릿 공유."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")
pytest.importorskip("sqlalchemy")

import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.schemas.request import ParsedPrompt
from app.services.segmentation import SegmentationResult


def _settings(**values) -> Settings:
    return Settings.model_validate({"DB_DIALECT": "sqlite", "PRELOAD_MODELS": False, **values})


class _MaskSegmentor:
    """호출 번호가 2일 때만 빈 마스크. 나머지는 중앙 사각형."""

    def __init__(self) -> None:
        self.calls = 0

    def predict(self, image, targets=None, min_confidence=None):
        self.calls += 1
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        if self.calls != 2:
            mask[4:20, 4:20] = 255
        return SegmentationResult(
            mask=mask,
            confidences=[0.9],
            labels=list(targets or ["person"]),
            backend="stub",
        )


def test_video_holds_previous_mask(tmp_path):
    from app.services.video_processor import process_video

    src = tmp_path / "in.avi"
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    writer = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (32, 32))
    assert writer.isOpened()
    for index in range(4):
        shot = frame.copy()
        shot[:, :] = (index * 40, 80, 20)
        writer.write(shot)
    writer.release()

    segmentor = _MaskSegmentor()
    info = process_video(
        src,
        tmp_path / "out.avi",
        ParsedPrompt(target=["person"], effect="blur", intensity=15),
        segmentor,
        max_frames=10,
        max_seconds=5,
    )
    assert info["frames"] == 4
    assert info["held"] == 1
    assert (tmp_path / "out.avi").stat().st_size > 0
    replay = cv2.VideoCapture(str(tmp_path / "out.avi"))
    ok, _ = replay.read()
    replay.release()
    assert ok


def test_batch_job_updates_progress(tmp_path, monkeypatch):
    import app.models  # noqa: F401
    from app.core.config import get_settings
    from app.db.base import Base
    from app.repositories.batch_repository import BatchRepository
    from app.services.image_processor import ImageProcessor
    from app.tasks.batch_tasks import run_batch_job, write_manifest
    from app.workflows import nodes

    settings = _settings(
        UPLOAD_DIR=str(tmp_path / "uploads"),
        YOLO_MODEL_PATH="models/missing-phase2.pt",
        LLM_PROVIDER="heuristic",
    )
    # 파이프라인은 전역 설정·공용 세그 싱글톤을 쓴다 → 같은 임시 폴더·가짜 세그를 꽂는다
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(nodes, "_processor", ImageProcessor(settings, segmentor=_MaskSegmentor()))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[:, :] = (0, 180, 40)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    job_id = "batchjob1"
    root = settings.upload_path / "batches" / job_id / "items"
    root.mkdir(parents=True)
    (root / "0000.jpg").write_bytes(encoded.tobytes())
    bad = root / "0001.jpg"
    bad.write_bytes(b"not-an-image")
    write_manifest(
        job_id,
        [
            {"index": 0, "filename": "a.jpg", "relpath": "items/0000.jpg"},
            {"index": 1, "filename": "b.jpg", "relpath": "items/0001.jpg"},
        ],
        settings=settings,
    )
    db = Session()
    BatchRepository(db).create(
        batch_id=job_id,
        prompt="person blur",
        total=2,
        status="queued",
        message="대기",
    )
    db.close()

    result = run_batch_job(
        job_id,
        session_factory=Session,
        settings=settings,
        parsed=ParsedPrompt(target=["person"], effect="blur", intensity=15),
    )
    assert result["status"] == "done"
    assert result["completed"] == 2
    assert "실패 1/2" in result["message"]
    check = Session()
    row = BatchRepository(check).get(job_id)
    assert row is not None
    assert row.progress == 1.0
    assert row.status == "done"
    assert len(row.item_results) == 2
    assert row.item_results[0]["status"] in {"ok", "fallback"}
    assert row.item_results[1]["status"] == "failed"
    assert row.item_results[0]["output"] and (settings.upload_path / "batches" / job_id / row.item_results[0]["output"]).is_file()
    assert not [p for p in settings.upload_path.iterdir() if p.name != "batches"]  # 처리용 임시 작업 폴더는 남기지 않는다
    check.close()


def test_enqueue_respects_flag(monkeypatch):
    from app.tasks import batch_tasks

    monkeypatch.setattr(batch_tasks, "celery", object())
    monkeypatch.setattr(batch_tasks, "run_batch_job_task", object())
    settings = batch_tasks.get_settings()
    monkeypatch.setattr(settings, "batch_use_celery", False)
    assert batch_tasks.enqueue_batch("job") is False
    monkeypatch.setattr(settings, "batch_use_celery", True)
    monkeypatch.setattr(batch_tasks, "celery", None)
    assert batch_tasks.enqueue_batch("job") is False


def test_stub_without_files_stays_unimplemented():
    from app.tasks.batch_tasks import process_batch_stub

    out = process_batch_stub("missing-batch-id", [{"filename": "a.jpg"}])
    assert out["status"] == "not_implemented"
    assert out["completed"] == 0


def test_open_vocab_disabled_raises():
    from app.services.segmentation import predict_grounding_sam2

    settings = _settings(OPEN_VOCAB_ENABLED=False)
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    with pytest.raises(NotImplementedError):
        predict_grounding_sam2(image, "dog", settings=settings)


def test_open_vocab_falls_through_without_weights(monkeypatch):
    from app.services.segmentation import Segmentor

    settings = _settings(
        OPEN_VOCAB_ENABLED=True,
        YOLO_MODEL_PATH="models/missing-phase2.pt",
    )
    segmentor = Segmentor(settings)

    def boom(*_args, **_kwargs):
        raise NotImplementedError("no weights")

    monkeypatch.setattr("app.services.segmentation.predict_grounding_sam2", boom)
    image = np.zeros((24, 24, 3), dtype=np.uint8)
    result = segmentor.predict(image, targets=["spaceship"])
    assert result.backend == "stub"


def test_open_vocab_used_for_unknown_label(monkeypatch):
    from app.services.segmentation import Segmentor

    settings = _settings(
        OPEN_VOCAB_ENABLED=True,
        YOLO_MODEL_PATH="models/missing-phase2.pt",
    )
    segmentor = Segmentor(settings)

    def ok(image, prompt, settings=None):
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[:, :] = 255
        return SegmentationResult(
            mask=mask,
            confidences=[0.8],
            labels=["spaceship"],
            backend="dino_sam2",
        )

    monkeypatch.setattr("app.services.segmentation.predict_grounding_sam2", ok)
    result = segmentor.predict(np.zeros((16, 16, 3), dtype=np.uint8), targets=["spaceship"])
    assert result.backend == "dino_sam2"


def test_known_class_skips_open_vocab():
    from app.services.segmentation import Segmentor

    settings = _settings(OPEN_VOCAB_ENABLED=True, YOLO_MODEL_PATH="models/missing-phase2.pt")
    segmentor = Segmentor(settings)
    segmentor._yolo = type("YoloNames", (), {"names": {0: "person", 1: "dog"}})()
    assert segmentor._needs_open_vocab(["person"]) is False
    assert segmentor._needs_open_vocab(["spaceship"]) is True
    segmentor.settings.open_vocab_enabled = False
    assert segmentor._needs_open_vocab(["spaceship"]) is False


def test_dino_text_joins_labels():
    from app.services.segmentation import _dino_text

    assert _dino_text("dog, cat") == "dog . cat ."


def test_open_vocab_drops_unmatched_boxes():
    """문구와 이어지지 않은 박스(빈 라벨)는 지울 대상이 아니다."""
    from app.services.segmentation import _keep_matched

    boxes, scores, labels = _keep_matched([[0, 0, 1, 1], [1, 1, 2, 2], [2, 2, 3, 3]], [0.9, 0.5, 0.4], ["helmet", "", " "])
    assert boxes == [[0, 0, 1, 1]] and scores == [0.9] and labels == ["helmet"]


def test_open_vocab_thresholds_are_separate_from_yolo():
    """DINO 후처리에는 YOLO MIN_CONFIDENCE 가 아니라 오픈보캐브 전용 임계값이 들어간다."""
    from app.services.segmentation import _post_dino

    seen = {}

    class _Proc:
        def post_process_grounded_object_detection(self, **kw):
            seen.update(kw)
            return [{}]

    inputs = type("Inputs", (), {"input_ids": None})()
    settings = _settings(OPEN_VOCAB_BOX_THRESHOLD=0.4, OPEN_VOCAB_TEXT_THRESHOLD=0.3, MIN_CONFIDENCE=0.25)
    _post_dino(_Proc(), None, inputs, settings.open_vocab_box_threshold, settings.open_vocab_text_threshold, (4, 4))
    assert seen["threshold"] == 0.4 and seen["text_threshold"] == 0.3


def test_open_vocab_warmup_skipped_when_disabled():
    from app.services.segmentation import warmup_open_vocab

    assert warmup_open_vocab(_settings(OPEN_VOCAB_ENABLED=False)) is False


def test_lora_template_is_shared_with_training():
    """서빙 prompt_spec.LORA_TEMPLATE 과 학습 템플릿이 같은 객체인지.

    이 커밋은 prompt_spec 을 바꾸지 않는다. 템플릿이 같으면 LoRA 재학습은 필요 없다.
    """
    import importlib.util
    import sys

    from app.services.prompt_spec import LORA_TEMPLATE

    repo = Path(__file__).resolve().parents[2]
    path = repo / "training" / "lora" / "dataset.py"
    spec = importlib.util.spec_from_file_location("lora_dataset_phase2_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.DEFAULT_INSTRUCTION_TEMPLATE is LORA_TEMPLATE
    assert "{prompt}" in LORA_TEMPLATE and "{response}" in LORA_TEMPLATE
