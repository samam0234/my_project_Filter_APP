# -*- coding: utf-8 -*-
"""작업실 "처리하기" 옆 해석 모델 선택 (services/llm_models · routers/llm · 사진 · GIF · 영상 연결).

Ollama 는 가짜로 — 설치된 모델 목록(/api/tags)만 흉내 내고 실제 네트워크는 쓰지 않는다.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.core.config import Settings, get_settings
from app.schemas.request import ParsedPrompt
from app.schemas.response import ProcessResult
from app.services import llm_models


def _settings(**env) -> Settings:
    return Settings(**{"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "gemma4:e4b", **env})


@pytest.fixture()
def tags(monkeypatch):
    """Ollama 에 설치된 모델을 바꿔 가며 쓰는 가짜. names 가 None 이면 Ollama 꺼짐."""
    state = {"names": {"gemma4:e4b", "gemma4:12b"}}
    monkeypatch.setattr(llm_models, "_cache", (0.0, None))
    monkeypatch.setattr(
        llm_models,
        "installed",
        lambda settings, *, force=False: None if state["names"] is None else frozenset(state["names"]),
    )
    return state


def _by_id(listing: dict) -> dict:
    return {m["id"]: m for m in listing["models"]}


def test_listing_marks_uninstalled_model_as_unavailable(tags):
    out = llm_models.listing(_settings())
    assert out["enabled"] and out["reachable"] and out["default"] == "gemma4:e4b"
    assert [(m["id"], m["available"]) for m in out["models"]] == [
        ("gemma4:e4b", True),
        ("gemma4:12b", True),
        ("qwen3.8:27b", False),  # 27b 는 설치 전이라 "미적용"
    ]
    assert [m["label"] for m in out["models"]] == ["Ollama e4b", "Ollama 12b", "Qwen 3.8 · 27b"]


def test_downloading_removes_the_unapplied_mark(tags):
    assert not _by_id(llm_models.listing(_settings()))["qwen3.8:27b"]["available"]
    tags["names"].add("qwen3.8:27b")  # 사용자가 ollama pull 로 내려받음
    assert _by_id(llm_models.listing(_settings()))["qwen3.8:27b"]["available"]
    assert llm_models.validate("qwen3.8:27b", _settings()) == "qwen3.8:27b"


def test_default_model_stays_selectable_when_ollama_is_down(tags):
    tags["names"] = None
    out = llm_models.listing(_settings())
    assert out["reachable"] is False
    assert [(m["id"], m["available"]) for m in out["models"]] == [
        ("gemma4:e4b", True),
        ("gemma4:12b", False),
        ("qwen3.8:27b", False),
    ]
    assert llm_models.validate("gemma4:e4b", _settings()) is None  # 기본은 늘 된다
    with pytest.raises(llm_models.ModelNotAvailable, match="연결할 수 없"):
        llm_models.validate("gemma4:12b", _settings())


def test_validate_rejects_unknown_and_uninstalled(tags):
    s = _settings()
    assert llm_models.validate(None, s) is None and llm_models.validate("  ", s) is None
    assert llm_models.validate("gemma4:12b", s) == "gemma4:12b"
    with pytest.raises(llm_models.ModelNotAvailable, match="지원하지 않는"):
        llm_models.validate("evil:latest", s)  # 목록 밖 이름은 Ollama 로 보내지 않는다
    with pytest.raises(llm_models.ModelNotAvailable, match="미적용"):
        llm_models.validate("qwen3.8:27b", s)


def test_selection_is_ignored_when_ollama_does_not_interpret(tags):
    s = _settings(LLM_PROVIDER="lora")  # GPU 서버: 해석은 LoRA — 선택은 의미가 없다
    assert llm_models.listing(s)["enabled"] is False
    assert llm_models.validate("gemma4:12b", s) is None
    assert llm_models.validate("qwen3.8:27b", s) is None  # 설치 안 됐어도 에러가 아니다


def test_configured_default_not_in_catalog_is_added_first(tags):
    s = _settings(OLLAMA_MODEL="llama3.2:3b")
    ids = [m["id"] for m in llm_models.listing(s)["models"]]
    assert ids[0] == "llama3.2:3b" and ids[1:] == ["gemma4:e4b", "gemma4:12b", "qwen3.8:27b"]


def test_with_model_copies_settings_and_lengthens_timeout():
    base = _settings(LLM_TIMEOUT_SECONDS=30)
    assert llm_models.with_model(base, None) is base
    big = llm_models.with_model(base, "qwen3.8:27b")
    assert (big.ollama_model, big.llm_timeout_seconds) == ("qwen3.8:27b", 180.0)
    assert (base.ollama_model, base.llm_timeout_seconds) == ("gemma4:e4b", 30.0)  # 서버 설정은 그대로
    assert llm_models.with_model(_settings(LLM_TIMEOUT_SECONDS=300), "gemma4:12b").llm_timeout_seconds == 300  # 더 긴 쪽


def test_prompt_analyzer_uses_the_chosen_model(monkeypatch, tags):
    """고른 모델이 실제 Ollama 요청의 model 로 간다 (사진 파이프라인 노드)."""
    from app.services import prompt_llm
    from app.workflows import nodes

    sent: list[tuple[str, float]] = []
    answer = {"message": {"content": '{"target":["person"],"effect":"remove_bg","intensity":15,"crop":false,"selector":null}'}}

    def fake_post(url, payload, timeout=30, **kw):
        sent.append((payload["model"], timeout))
        return answer

    monkeypatch.setattr(prompt_llm, "_post_json", fake_post)
    s = get_settings()
    monkeypatch.setattr(s, "llm_provider", "ollama")
    monkeypatch.setattr(s, "prompt_chain", "legacy")
    monkeypatch.setattr(s, "prompt_rag_enabled", False)
    out = nodes.prompt_analyzer({"job_id": "t1", "prompt": "사람만 남겨줘", "llm_model": "gemma4:12b"})
    assert sent[-1][0] == "gemma4:12b" and sent[-1][1] >= 90
    assert out["llm_model"] == "gemma4:12b" and out["prompt_parser"] == "ollama"
    nodes.prompt_analyzer({"job_id": "t2", "prompt": "사람만 남겨줘"})
    assert sent[-1][0] == s.ollama_model  # 안 골랐으면 서버 기본
    assert get_settings().ollama_model == s.ollama_model  # 요청이 서버 설정을 바꾸지 않았다


# ------------------------------------------------------------------ HTTP


def _jpeg() -> bytes:
    ok, buf = cv2.imencode(".jpg", np.full((32, 48, 3), 120, np.uint8))
    return buf.tobytes()


@pytest.fixture()
def api(api_env, monkeypatch, tags):
    s = get_settings()
    monkeypatch.setattr(s, "llm_provider", "ollama")
    monkeypatch.setattr(s, "ollama_model", "gemma4:e4b")
    seen: list[dict] = []

    def fake_pipeline(image_bytes, prompt, job_id=None, persist=True, **kw):
        seen.append(kw)
        return ProcessResult(
            job_id="zzmodel0001",
            status="ok",
            quality_score=0.9,
            message="ok",
            parsed_prompt=ParsedPrompt(target=["person"], effect="remove_bg"),
            before_path=None,
            after_path=None,
        )

    import app.routers.upload as upload_router

    monkeypatch.setattr(upload_router, "run_pipeline", fake_pipeline)
    return api_env["client"], seen


def test_models_endpoint_is_public(api):
    client, _ = api
    body = client.get("/api/v1/llm/models").json()
    assert body["enabled"] and _by_id(body)["qwen3.8:27b"]["available"] is False


def test_upload_passes_chosen_model_only_when_not_default(api):
    client, seen = api
    files = {"file": ("a.jpg", _jpeg(), "image/jpeg")}
    assert client.post("/api/v1/upload", files=files, data={"prompt": "사람만", "llm_model": "gemma4:12b"}).status_code == 200
    assert seen[-1] == {"llm_model": "gemma4:12b"}
    for data in ({"prompt": "사람만"}, {"prompt": "사람만", "llm_model": "gemma4:e4b"}):
        assert client.post("/api/v1/upload", files=files, data=data).status_code == 200
        assert seen[-1] == {}  # 기본이면 인자를 넘기지 않는다


def test_upload_rejects_uninstalled_or_unknown_model(api):
    client, seen = api
    files = {"file": ("a.jpg", _jpeg(), "image/jpeg")}
    r = client.post("/api/v1/upload", files=files, data={"prompt": "사람만", "llm_model": "qwen3.8:27b"})
    assert r.status_code == 400 and "미적용" in r.json()["detail"]
    r = client.post("/api/v1/upload", files=files, data={"prompt": "사람만", "llm_model": "evil:latest"})
    assert r.status_code == 400 and "지원하지 않는" in r.json()["detail"]
    assert seen == []  # 파이프라인까지 가지 않았다


def test_gif_and_video_validate_the_model_too(api):
    client, _ = api
    gif = b"GIF89a" + b"\0" * 20
    r = client.post("/api/v1/gif", files={"file": ("a.gif", gif, "image/gif")}, data={"prompt": "사람만", "llm_model": "qwen3.8:27b"})
    assert r.status_code == 400 and "미적용" in r.json()["detail"]
    r = client.post("/api/v1/video", files={"file": ("a.mp4", b"\0" * 20, "video/mp4")}, data={"prompt": "사람만", "llm_model": "evil:x"})
    assert r.status_code == 400 and "지원하지 않는" in r.json()["detail"]
