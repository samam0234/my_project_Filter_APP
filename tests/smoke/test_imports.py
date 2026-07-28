# -*- coding: utf-8 -*-
"""핵심 모듈 import 스모크 (패키지 설치 환경에서).

의존성이 없으면 importorskip 으로 건너뛴다.
CI 에서 최소 기동 가능 여부만 빠르게 확인하는 용도.
"""

from __future__ import annotations

import pytest


def test_import_constants():
    """상수 모듈 로드 및 Phase 1 값 확인."""
    from app.core import constants

    assert constants.PHASE == 1
    assert constants.API_V1_PREFIX == "/api/v1"


def test_import_schemas():
    """Pydantic 스키마 패키지 import."""
    pytest.importorskip("pydantic")
    from app.schemas import request, response, feedback  # noqa: F401


def test_import_workflow_nodes():
    """워크플로 노드(휴리스틱 파서) 호출 가능 여부."""
    pytest.importorskip("pydantic")
    from app.workflows import nodes

    assert callable(nodes.parse_prompt_heuristic)


def test_import_services_optional():
    """validator 등 numpy 의존 서비스."""
    pytest.importorskip("numpy")
    from app.services import validator  # noqa: F401


def test_import_fastapi_app():
    """FastAPI 앱 팩토리 create_app() 기동 스모크."""
    pytest.importorskip("fastapi")
    pytest.importorskip("pydantic_settings")
    # SQLAlchemy 미설치 환경에서는 스킵
    pytest.importorskip("sqlalchemy")
    from app.main import create_app

    app = create_app()
    assert app.title  # 앱 제목 존재 (Cut & Keep)
