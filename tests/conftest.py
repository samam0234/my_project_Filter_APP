# -*- coding: utf-8 -*-
"""pytest 공통 설정."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 저장소 루트 · backend 를 import 경로에 추가
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"

for p in (str(BACKEND_ROOT), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def backend_root() -> Path:
    return BACKEND_ROOT
