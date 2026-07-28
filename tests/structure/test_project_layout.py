# -*- coding: utf-8 -*-
"""프로젝트 폴더·핵심 파일 존재 검사 (의존성 거의 불필요).

문서/스캐폴드 누락을 조기에 잡기 위한 구조 테스트.
"""

from __future__ import annotations

from pathlib import Path


def test_root_dirs(repo_root: Path):
    """루트에 필수 디렉터리가 있는지."""
    required = [
        "backend",
        "frontend",
        "console",
        "docs",
        "training",
        "tests",
        "scripts",
        "data",
        "models",
        "logs",
        "docker",
    ]
    for name in required:
        assert (repo_root / name).is_dir(), f"missing dir: {name}"


def test_backend_app_layout(repo_root: Path):
    """backend/app 계층(main, core, db, ...) 존재."""
    app = repo_root / "backend" / "app"
    for name in [
        "main.py",
        "core",
        "db",
        "models",
        "schemas",
        "repositories",
        "routers",
        "services",
        "workflows",
        "utils",
    ]:
        p = app / name
        assert p.exists(), f"missing backend path: {p}"


def test_training_layout(repo_root: Path):
    """학습 구역 스크립트·설정 예시 파일."""
    t = repo_root / "training"
    assert (t / "README.md").is_file()
    assert (t / "yolo" / "train_segment.py").is_file()
    assert (t / "yolo" / "train_detect.py").is_file()
    assert (t / "yolo" / "export_onnx.py").is_file()
    assert (t / "lora" / "train_lora.py").is_file()
    assert (t / "configs" / "dataset_seg.example.yaml").is_file()
    assert (t / "requirements-training.txt").is_file()


def test_docs_plan_files(repo_root: Path):
    """docs/plan 핵심 설계 문서."""
    plan = repo_root / "docs" / "plan"
    for name in [
        "LOGIC_STRUCTURE.md",
        "PROJECT_STRUCTURE.md",
        "DATABASE.md",
        "AI_MODEL_STRATEGY.md",
        "LOGIC_AND_GIT_BRANCH_STRATEGY.md",
        "DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md",
        "TESTING.md",
    ]:
        assert (plan / name).is_file(), f"missing plan doc: {name}"


def test_docs_hub_folders(repo_root: Path):
    """문서 허브 하위 폴더 + README."""
    docs = repo_root / "docs"
    for name in [
        "Architecture",
        "branchs",
        "guidance",
        "find_debug",
        "trainings",
        "repeater",
        "vaildates",
        "web_management",
    ]:
        assert (docs / name).is_dir(), f"missing docs/{name}"
        assert (docs / name / "README.md").is_file()


def test_agent_skill_layout(repo_root: Path):
    """에이전트 규칙·스킬 경로."""
    assert (repo_root / "AGENTS.md").is_file()
    assert (repo_root / ".agents" / "skills" / "cutnkeep" / "SKILL.md").is_file()
    assert (repo_root / ".grok" / "skills" / "cutnkeep" / "SKILL.md").is_file()


def test_env_example_and_run_guide(repo_root: Path):
    """환경 예시·실행 가이드·pytest 설정."""
    assert (repo_root / ".env.example").is_file()
    assert (repo_root / "RUN.md").is_file()
    assert (repo_root / "pytest.ini").is_file()


def test_folder_readmes(repo_root: Path):
    """주요 폴더 README 존재."""
    for name in [
        "backend",
        "frontend",
        "console",
        "scripts",
        "training",
        "tests",
        "data",
        "models",
        "logs",
    ]:
        assert (repo_root / name / "README.md").is_file(), f"README missing: {name}"
