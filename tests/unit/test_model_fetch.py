# -*- coding: utf-8 -*-
"""큰 모델 파일 받기 (services/model_fetch) · LaMa 가 나중에 생겨도 로드 (services/inpaint).

네트워크 없이 file:// 주소로 흉내 낸다.
"""

from __future__ import annotations

import hashlib

import pytest

from app.core.config import Settings
from app.services import inpaint, model_fetch


@pytest.fixture()
def fake_model(tmp_path, monkeypatch):
    src = tmp_path / "remote.onnx"
    src.write_bytes(b"fake-onnx-model" * 1000)
    spec = model_fetch.ModelFile(
        name="lama", url=src.as_uri(), sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
        size=src.stat().st_size, license="test",
    )
    monkeypatch.setitem(model_fetch.MODELS, "lama", spec)
    settings = Settings.model_validate({"INPAINT_MODEL_PATH": str(tmp_path / "models" / "lama_fp32.onnx")})
    return settings, spec


def test_fetch_downloads_and_verifies(fake_model):
    settings, spec = fake_model
    path = model_fetch.fetch("lama", settings)
    assert path.read_bytes() == b"fake-onnx-model" * 1000
    assert not list(path.parent.glob("*.part"))
    assert model_fetch.fetch("lama", settings) == path  # 이미 있고 맞으면 건너뜀


def test_fetch_rejects_checksum_mismatch(fake_model, monkeypatch):
    settings, spec = fake_model
    monkeypatch.setitem(model_fetch.MODELS, "lama", model_fetch.ModelFile(**{**spec.__dict__, "sha256": "0" * 64}))
    with pytest.raises(ValueError, match="체크섬"):
        model_fetch.fetch("lama", settings)
    folder = settings.inpaint_model_file.parent
    assert not settings.inpaint_model_file.exists() and not list(folder.glob("*.part"))


def test_background_fetch_only_when_needed(fake_model):
    settings, _ = fake_model
    assert model_fetch.start_background(settings.model_copy(update={"model_auto_download": False})) is False
    assert model_fetch.start_background(settings.model_copy(update={"inpaint_engine": "telea"})) is False
    settings.inpaint_model_file.parent.mkdir(parents=True)
    settings.inpaint_model_file.write_bytes(b"x")
    assert model_fetch.start_background(settings) is False  # 이미 있으면 받지 않는다


def test_inpaint_loads_once_file_appears(tmp_path, monkeypatch):
    """기동 때 없던 모델이 나중에 생기면(자동 받기) 그때 로드한다 — 한 번 없다고 영영 Telea 로 남지 않게."""
    settings = Settings.model_validate({"INPAINT_MODEL_PATH": str(tmp_path / "lama.onnx")})
    monkeypatch.setattr(inpaint, "_SESSION", None)
    monkeypatch.setattr(inpaint, "_FAILED", None)
    loads = []
    import app.utils.onnx_utils as onnx_utils

    monkeypatch.setattr(onnx_utils, "create_session", lambda path, providers: loads.append(path) or object())
    assert inpaint._session(settings) is None
    (tmp_path / "lama.onnx").write_bytes(b"model")
    assert inpaint._session(settings) is not None and len(loads) == 1
    assert inpaint._session(settings) is not None and len(loads) == 1  # 한 번만 로드
