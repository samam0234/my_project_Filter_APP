# -*- coding: utf-8 -*-
"""Pydantic 스키마 기본 검증."""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from app.schemas.request import ParsedPrompt, UploadFormMeta
from app.schemas.response import HealthResponse, ProcessResult, UploadResponse
from app.schemas.feedback import FeedbackRequest
from app.core.constants import FeedbackVote


def test_parsed_prompt_defaults():
    p = ParsedPrompt()
    assert p.target == ["person"]
    assert p.effect == "remove_bg"
    assert 0 <= p.intensity <= 100
    assert p.crop is False


def test_parsed_prompt_custom():
    p = ParsedPrompt(target=["dog"], effect="blur", intensity=20, crop=True)
    assert p.target == ["dog"]
    assert p.effect == "blur"
    assert p.intensity == 20
    assert p.crop is True


def test_parsed_prompt_intensity_bounds():
    with pytest.raises(Exception):
        ParsedPrompt(intensity=101)
    with pytest.raises(Exception):
        ParsedPrompt(intensity=-1)


def test_upload_form_meta_requires_prompt():
    with pytest.raises(Exception):
        UploadFormMeta(prompt="")


def test_health_response():
    h = HealthResponse()
    assert h.status == "ok"
    assert h.phase == 1


def test_process_and_upload_response():
    pr = ProcessResult(job_id="abc", status="ok")
    assert pr.job_id == "abc"
    ur = UploadResponse(job_id="abc", status="ok", quality_score=0.5)
    assert ur.quality_score == 0.5


def test_feedback_request():
    fb = FeedbackRequest(job_id="j1", vote=FeedbackVote.LIKE)
    assert fb.vote == FeedbackVote.LIKE
