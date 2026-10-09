# -*- coding: utf-8 -*-
"""배포 리허설 도구 (scripts/deploy_check.py · scripts/models_bundle.py) — 네트워크 · Docker 없이 판단 부분만."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


deploy_check = _load("deploy_check")
models_bundle = _load("models_bundle")


def test_report_counts_fail_and_warn(capsys):
    rep = deploy_check.Report()
    assert rep.check(True, "좋음", "나쁨")
    assert not rep.check(False, "좋음", "나쁨")
    assert not rep.check(False, "좋음", "주의", warn_only=True)
    assert (rep.fails, rep.warns) == (1, 1)
    out = capsys.readouterr().out
    assert "✓ 좋음" in out and "✗ 나쁨" in out and "! 주의" in out


def test_env_parsing_ignores_comments_and_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# 주석\nAPP_ENV=production\nSECRET_KEY='abc=def'\n\nDOMAIN=\"x.example\"\n", encoding="utf-8")
    assert deploy_check._env(env) == {"APP_ENV": "production", "SECRET_KEY": "abc=def", "DOMAIN": "x.example"}


def test_bundle_picks_only_configured_models(monkeypatch, tmp_path):
    backend = tmp_path / "backend"
    (backend / "models" / "lora").mkdir(parents=True)
    (backend / "models" / "lora" / "adapter_model.safetensors").write_bytes(b"w")
    monkeypatch.setattr(models_bundle, "BACKEND", backend)
    base = {"YOLO_MODEL_PATH": "models/yolo26m-seg.onnx"}
    names = [p.name for p in models_bundle.wanted_files(base)]
    assert names == ["yolo26m-seg.onnx", "segformer-ade.onnx", "segformer-ade.labels.json", "lama_fp32.onnx"]
    with_lora = [p.name for p in models_bundle.wanted_files({**base, "LLM_PROVIDER": "lora"})]
    assert "adapter_model.safetensors" in with_lora  # LoRA 를 쓸 때만 어댑터를 묶는다


def test_bundle_verify_detects_changed_file(monkeypatch, tmp_path):
    f = tmp_path / "backend" / "models" / "a.onnx"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"model-v1")
    monkeypatch.setattr(models_bundle, "ROOT", tmp_path)
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"files": {"backend/models/a.onnx": models_bundle.sha256(f)}}), encoding="utf-8")
    args = type("A", (), {"manifest": str(manifest)})()
    assert models_bundle.verify(args) == 0
    f.write_bytes(b"model-v2")
    assert models_bundle.verify(args) == 1


def test_gpu_bundle_adds_lora_adapter_and_base_model(monkeypatch, tmp_path):
    backend = tmp_path / "backend"
    (backend / "models" / "lora").mkdir(parents=True)
    (backend / "models" / "lora" / "adapter_model.safetensors").write_bytes(b"a")
    base = tmp_path / "training" / "models" / "qwen2.5-1.5b-instruct"
    base.mkdir(parents=True)
    (base / "model.safetensors").write_bytes(b"b")
    (base / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(models_bundle, "BACKEND", backend)
    monkeypatch.setattr(models_bundle, "ROOT", tmp_path)
    monkeypatch.setattr(models_bundle, "GPU_BASE", base)
    cpu = [p.name for p in models_bundle.wanted_files({})]
    gpu = [p.name for p in models_bundle.wanted_files({}, gpu=True)]
    assert "adapter_model.safetensors" not in cpu and "model.safetensors" not in cpu
    assert {"adapter_model.safetensors", "model.safetensors", "config.json"} <= set(gpu)  # GPU 오버레이는 compose 가 lora 를 켠다


make_prod_env = _load("make_prod_env")


def test_set_replaces_value_or_uncomments_example():
    lines = ["APP_ENV=development", "# DOMAIN=cnk.example.com", "X=1"]
    lines = make_prod_env._set(lines, "APP_ENV", "production")
    lines = make_prod_env._set(lines, "DOMAIN", "a.example")
    lines = make_prod_env._set(lines, "NEW", "v")
    assert lines == ["APP_ENV=production", "# DOMAIN=cnk.example.com", "DOMAIN=a.example", "X=1", "NEW=v"]


def test_prod_env_passes_preflight_and_keeps_secrets_out_of_args(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CNK_SMTP_PASSWORD", "from-env-only")
    out = tmp_path / ".env.production"
    monkeypatch.setattr("sys.argv", ["x", "--out", str(out), "--domain", "a.example", "--acme-email", "o@a.example",
                                     "--smtp-host", "smtp.a.example", "--smtp-port", "465", "--smtp-user", "m@a.example",
                                     "--console-admins", "admin"])
    assert make_prod_env.main() == 0
    env = deploy_check._env(out)
    assert env["APP_ENV"] == "production" and env["DEBUG"] == "false" and env["SESSION_COOKIE_SECURE"] == "true"
    assert env["CORS_ORIGINS"] == "https://a.example" and env["SMTP_SSL"] == "true" and env["SMTP_STARTTLS"] == "false"
    assert env["SMTP_PASSWORD"] == "from-env-only" and len(env["SECRET_KEY"]) >= 32
    assert env["MARIADB_PASSWORD"] not in ("change-me-db-password", "") and env["LEARNING_DB_FALLBACK_SQLITE"] == "false"
    assert "오류 0" in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["x", "--out", str(out), "--domain", "a.example", "--acme-email", "o@a.example",
                                     "--smtp-host", "smtp.a.example"])
    assert make_prod_env.main() == 1  # 있으면 덮어쓰지 않는다 (비밀 값이 바뀌므로)
