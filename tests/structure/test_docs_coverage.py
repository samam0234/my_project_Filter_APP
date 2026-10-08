# -*- coding: utf-8 -*-
"""기능 문서 등록 검사 — 코드에 생긴 기능이 문서에 빠지지 않게.

- 모든 API 엔드포인트가 docs/API_DOCUMENTATION.md 에 있다
- 모든 설정(Settings 의 alias)이 .env.example 에 있다 (주석 처리된 예시 포함)
- 모든 설정이 문서 어딘가에서 설명된다
- 사용자 앱의 모든 화면 경로가 사용자 가이드 · frontend README 에 있다
- 기능 목록 docs/FEATURES.md 가 모든 화면 경로를 담는다
새 기능을 넣고 이 테스트가 실패하면, 실패 메시지에 나온 항목을 해당 문서에 적는다.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _norm(path: str) -> str:
    """경로 변수 이름 차이({id} vs {job_id})는 무시한다."""
    return re.sub(r"\{[^}]+\}", "{}", path)


def _endpoints() -> list[tuple[str, str]]:
    found = []
    for f in sorted((ROOT / "backend/app/routers").glob("*.py")):
        s = f.read_text(encoding="utf-8")
        prefix = re.search(r'APIRouter\([^)]*prefix="([^"]+)"', s)
        prefix = prefix.group(1) if prefix else ""
        for m in re.finditer(r'@router\.(get|post|put|patch|delete)\("([^"]*)"', s):
            found.append((m.group(1).upper(), "/api/v1" + prefix + m.group(2)))
    return found


def _aliases() -> list[str]:
    return re.findall(r'alias="([A-Z0-9_]+)"', _read("backend/app/core/config.py"))


def _all_docs() -> str:
    paths = [p for p in (ROOT / "docs").rglob("*.md") if "branchs" not in p.parts]
    paths += [ROOT / "README.md", ROOT / "RUN.md", *ROOT.glob("*/README.md"), *ROOT.glob("backend/*/README.md")]
    return "\n".join(p.read_text(encoding="utf-8") for p in paths if p.is_file())


def test_every_endpoint_is_in_api_documentation():
    doc = _norm(_read("docs/API_DOCUMENTATION.md"))
    missing = [f"{m} {p}" for m, p in _endpoints() if _norm(p).replace("/api/v1", "") not in doc]
    assert len(_endpoints()) > 30
    assert not missing, "API 문서(docs/API_DOCUMENTATION.md)에 없는 엔드포인트: " + ", ".join(missing)


def test_every_setting_is_in_env_example():
    env = _read(".env.example")
    missing = [a for a in _aliases() if not re.search(rf"^\s*#?\s*{a}\s*=", env, re.M)]
    assert not missing, ".env.example 에 없는 설정: " + ", ".join(missing)


def test_every_setting_is_explained_in_docs():
    docs = _all_docs()
    missing = [a for a in _aliases() if a not in docs]
    assert not missing, "문서 어디에도 설명이 없는 설정: " + ", ".join(missing)


def _frontend_routes() -> list[str]:
    app = _read("frontend/src/App.tsx")
    return sorted({r for r in re.findall(r'["\'](/[a-z\-/:]*)["\']', app) if not r.endswith("/") or r == "/"})


def test_every_screen_is_in_user_guide():
    doc = _read("docs/guidance/user-frontend.md") + _read("frontend/README.md")
    assert len(_frontend_routes()) >= 10  # 경로를 못 읽으면 검사가 그냥 통과하지 않게
    missing = [r for r in _frontend_routes() if r != "/" and f"`{r}`" not in doc]
    assert not missing, "사용자 가이드 · frontend README 에 없는 화면: " + ", ".join(missing)


def test_feature_list_covers_screens_and_media_endpoints():
    features = _read("docs/FEATURES.md")
    missing = [r for r in _frontend_routes() if r != "/" and f"`{r}`" not in features]
    for path in ("/upload", "/gif", "/video", "/batch", "/feedback", "/jobs"):
        if path not in features:
            missing.append(path)
    assert not missing, "docs/FEATURES.md 에 없는 화면·API: " + ", ".join(missing)
