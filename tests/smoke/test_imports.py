# -*- coding: utf-8 -*-
"""핵심 모듈 import 스모크 (패키지 설치 환경에서)."""

from __future__ import annotations

import pytest


def test_import_constants():
    from app.core import constants

    assert constants.PHASE == 1
    assert constants.API_V1_PREFIX == "/api/v1"


def test_import_schemas():
    pytest.importorskip("pydantic")
    from app.schemas import request, response, feedback  # noqa: F401


def test_import_workflow_nodes():
    pytest.importorskip("pydantic")
    from app.workflows import nodes

    assert callable(nodes.parse_prompt_heuristic)


def test_import_services_optional():
    pytest.importorskip("numpy")
    from app.services import validator  # noqa: F401


def test_import_fastapi_app():
    pytest.importorskip("fastapi")
    pytest.importorskip("pydantic_settings")
    # SQLAlchemy 등 필요 시 skip
    pytest.importorskip("sqlalchemy")
    from app.main import create_app

    app = create_app()
    assert app.title  # Cut & Keep
