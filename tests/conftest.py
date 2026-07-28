# -*- coding: utf-8 -*-
"""pytest 공통 설정.

- backend/ 를 sys.path 에 넣어 `import app...` 가 동작하게 함
- session 스코프 fixture: repo_root, backend_root
실행 가이드: docs/plan/TESTING.md
"""

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
    """모노레포 루트 (CutNKeep/)."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def backend_root() -> Path:
    """backend/ 디렉터리."""
    return BACKEND_ROOT
