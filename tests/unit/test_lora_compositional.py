# -*- coding: utf-8 -*-
"""LoRA 조합형 시드 생성기(training/lora/seed/build_compositional.py) — 학습 없이 데이터 계약만 검증한다."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


comp = _load("build_compositional", REPO_ROOT / "training/lora/seed/build_compositional.py")

def test_korean_particles_follow_final_consonant():
    assert comp.j("고양이", "이랑") == "고양이랑" and comp.j("말", "이랑") == "말이랑"
    assert comp.j("건물", "은는") == "건물은" and comp.j("하늘", "을를") == "하늘을" and comp.j("소파", "을를") == "소파를"
    assert comp.j("사과", "과와") == "사과와" and comp.j("책", "과와") == "책과"


def test_compositional_labels_are_canonical_and_deterministic():
    from app.services.prompt_spec import normalize_parsed

    rows = comp.build(300)
    assert rows == comp.build(300)  # 같은 시드면 같은 문장
    assert len({r["prompt"] for r in rows}) == 300
    for r in rows:
        p = r["parsed_prompt"]
        assert normalize_parsed(p).target == p["target"]  # 서빙 규격과 같은 이름
        assert p["selector"] is None  # 관계 표현("X 옆의 Y")은 위치 selector 가 아니다
        assert p["crop"] == (p["effect"] == "crop" or "크롭까지" in r["prompt"] or "다음 잘라" in r["prompt"])


def test_compositional_file_excludes_eval_sentences():
    seed = REPO_ROOT / "training/lora/seed"
    evals = {json.loads(l)["prompt"].replace(" ", "").lower() for f in seed.glob("eval*.jsonl") for l in f.open(encoding="utf-8") if l.strip()}
    train = [json.loads(l)["prompt"].replace(" ", "").lower() for l in (seed / "train_compositional.jsonl").open(encoding="utf-8")]
    assert train and not (set(train) & evals)
