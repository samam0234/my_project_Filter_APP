# -*- coding: utf-8 -*-
"""프로젝트 폴더·핵심 파일 존재 검사 (의존성 거의 불필요)."""

from __future__ import annotations

from pathlib import Path


def test_root_dirs(repo_root: Path):
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
    t = repo_root / "training"
    assert (t / "README.md").is_file()
    assert (t / "yolo" / "train_segment.py").is_file()
    assert (t / "yolo" / "train_detect.py").is_file()
    assert (t / "yolo" / "export_onnx.py").is_file()
    assert (t / "lora" / "train_lora.py").is_file()
    assert (t / "configs" / "dataset_seg.example.yaml").is_file()
    assert (t / "requirements-training.txt").is_file()


def test_docs_plan_files(repo_root: Path):
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
    assert (repo_root / "AGENTS.md").is_file()
    assert (repo_root / ".agents" / "skills" / "cutnkeep" / "SKILL.md").is_file()
    assert (repo_root / ".grok" / "skills" / "cutnkeep" / "SKILL.md").is_file()


def test_env_example_and_run_guide(repo_root: Path):
    assert (repo_root / ".env.example").is_file()
    assert (repo_root / "RUN.md").is_file()
    assert (repo_root / "pytest.ini").is_file()


def test_folder_readmes(repo_root: Path):
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
