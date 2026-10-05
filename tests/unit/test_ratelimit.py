# -*- coding: utf-8 -*-
"""업로드 속도 제한 — 비로그인 IP · 회원 계정 기준, 429 + Retry-After."""

from __future__ import annotations

import pytest

from app.core.ratelimit import SlidingWindowLimiter


def test_sliding_window():
    lim = SlidingWindowLimiter(60.0)
    assert [lim.hit("a", 2, now=t) for t in (0, 1)] == [0.0, 0.0]
    assert lim.hit("a", 2, now=2) == pytest.approx(58.0)  # 첫 요청이 빠질 때까지
    assert lim.hit("b", 2, now=2) == 0.0  # 키별
    assert lim.hit("a", 2, now=60.5) == 0.0  # 창이 지나면 다시 허용
    assert lim.hit("a", 0, now=61) == 0.0  # 0 = 제한 없음


def test_guest_upload_is_limited_per_minute(api_env, monkeypatch):
    pytest.importorskip("cv2")
    import cv2
    import numpy as np

    from app.core.config import get_settings
    from app.routers import upload as upload_router
    from app.schemas.request import ParsedPrompt
    from app.schemas.response import ProcessResult

    def fake_pipeline(image_bytes, prompt, job_id=None, persist=True):
        return ProcessResult(job_id="zzrate", status="ok", quality_score=1.0, message="ok",
                             parsed_prompt=ParsedPrompt(target=["person"]))

    monkeypatch.setattr(upload_router, "run_pipeline", fake_pipeline)
    monkeypatch.setattr(get_settings(), "upload_rate_guest_per_min", 2)
    ok, buf = cv2.imencode(".jpg", np.zeros((8, 8, 3), np.uint8))

    def upload():
        return api_env["client"].post("/api/v1/upload", files={"file": ("a.jpg", buf.tobytes(), "image/jpeg")},
                                      data={"prompt": "사람만"})

    assert [upload().status_code for _ in range(2)] == [200, 200]
    r = upload()
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    assert "비로그인" in r.json()["detail"]
