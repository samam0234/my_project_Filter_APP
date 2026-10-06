# -*- coding: utf-8 -*-
"""training/lora/dataset.py — torch 없이 데이터 계약만 검증."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LORA_DIR = REPO_ROOT / "training" / "lora"
if str(LORA_DIR) not in sys.path:
    sys.path.insert(0, str(LORA_DIR))

from dataset import (  # noqa: E402
    comment_as_parsed,
    discover_feedback_cases,
    to_instruction_records,
    write_run_manifest,
)


def _write_case(folder: Path, stem: str, payload: dict) -> Path:
    path = folder / f"{stem}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_like_with_parsed_prompt_becomes_record(tmp_path: Path):
    """like + prompt + parsed_prompt → instruction 1건."""
    _write_case(
        tmp_path,
        "job1_aaaa",
        {
            "case_id": "job1_aaaa",
            "vote": "like",
            "source": "user",
            "meta": {
                "prompt": "강아지만 남기고 배경 블러",
                "parsed_prompt": {
                    "target": ["dog"],
                    "effect": "blur",
                    "intensity": 15,
                    "crop": False,
                },
            },
        },
    )
    cases = discover_feedback_cases(tmp_path)
    records = to_instruction_records(cases)
    assert len(cases) == 1
    assert len(records) == 1
    assert "강아지만 남기고 배경 블러" in records[0].text
    assert '"target":["dog"]' in records[0].response_json
    assert '"effect":"blur"' in records[0].response_json


def test_dislike_without_json_comment_is_skipped(tmp_path: Path):
    """dislike 는 시스템 parsed_prompt 를 정답으로 쓰지 않는다."""
    _write_case(
        tmp_path,
        "job2_bbbb",
        {
            "case_id": "job2_bbbb",
            "vote": "dislike",
            "comment": "마스크가 이상해요",
            "source": "user",
            "meta": {
                "prompt": "사람만 남기기",
                "parsed_prompt": {
                    "target": ["person"],
                    "effect": "remove_bg",
                    "intensity": 15,
                    "crop": False,
                },
            },
        },
    )
    records = to_instruction_records(discover_feedback_cases(tmp_path))
    assert records == []


def test_dislike_json_comment_is_correction(tmp_path: Path):
    """dislike 코멘트가 ParsedPrompt JSON 이면 그 값을 정답으로 쓴다."""
    _write_case(
        tmp_path,
        "job3_cccc",
        {
            "case_id": "job3_cccc",
            "vote": "dislike",
            "comment": '{"target":["cat"],"effect":"blur","intensity":20,"crop":false}',
            "source": "user",
            "meta": {
                "prompt": "고양이만 남기고 블러",
                "parsed_prompt": {
                    "target": ["dog"],
                    "effect": "remove_bg",
                    "intensity": 15,
                    "crop": False,
                },
            },
        },
    )
    records = to_instruction_records(discover_feedback_cases(tmp_path))
    assert len(records) == 1
    assert '"target":["cat"]' in records[0].response_json
    assert '"effect":"blur"' in records[0].response_json


def test_pipeline_failure_included_unless_skipped(tmp_path: Path):
    """pipeline_failure 는 기본 포함, 플래그면 제외."""
    _write_case(
        tmp_path,
        "job4_dddd",
        {
            "case_id": "job4_dddd",
            "vote": "dislike",
            "source": "pipeline_failure",
            "meta": {
                "prompt": "가방만 크롭",
                "parsed_prompt": {
                    "target": ["bag"],
                    "effect": "crop",
                    "intensity": 15,
                    "crop": True,
                },
            },
        },
    )
    cases = discover_feedback_cases(tmp_path)
    included = to_instruction_records(cases, include_pipeline_failure=True)
    excluded = to_instruction_records(cases, include_pipeline_failure=False)
    assert len(included) == 1
    assert excluded == []


def test_broken_json_is_skipped(tmp_path: Path):
    """깨진 사이드카는 예외 대신 건너뛴다."""
    (tmp_path / "bad.json").write_text("{not-json", encoding="utf-8")
    assert discover_feedback_cases(tmp_path) == []


def test_comment_as_parsed_extracts_embedded_json():
    """앞뒤 문장이 있어도 JSON 객체를 뽑아 정규화한다."""
    parsed = comment_as_parsed(
        '정답은 {"target":["car"],"effect":"none","intensity":0,"crop":false} 입니다'
    )
    assert parsed is not None
    assert parsed["target"] == ["car"]
    assert parsed["effect"] == "none"


def test_write_run_manifest(tmp_path: Path):
    """run.json 이 샘플을 남긴다."""
    _write_case(
        tmp_path,
        "job5_eeee",
        {
            "case_id": "job5_eeee",
            "vote": "like",
            "meta": {
                "prompt": "사람만 남기기",
                "parsed_prompt": {
                    "target": ["person"],
                    "effect": "remove_bg",
                    "intensity": 10,
                    "crop": False,
                },
            },
        },
    )
    records = to_instruction_records(discover_feedback_cases(tmp_path))
    out = tmp_path / "run.json"
    write_run_manifest(out, args={"epochs": 3}, summary={"records": 1}, records=records)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["records"] == 1
    assert data["samples"][0]["case_id"] == "job5_eeee"


def test_missing_dir_returns_empty(tmp_path: Path):
    """없는 폴더는 빈 리스트 (예외 없음)."""
    assert discover_feedback_cases(tmp_path / "nope") == []


@pytest.mark.skipif(
    not (LORA_DIR / "train_lora.py").is_file(),
    reason="train_lora.py 없음",
)
def test_dry_run_exits_zero_without_peft(tmp_path: Path):
    """--dry-run 은 peft 없이 exit 0, run.json 생성."""
    import subprocess

    _write_case(
        tmp_path,
        "job6_ffff",
        {
            "case_id": "job6_ffff",
            "vote": "like",
            "meta": {
                "prompt": "강아지",
                "parsed_prompt": {
                    "target": ["dog"],
                    "effect": "blur",
                    "intensity": 15,
                    "crop": False,
                },
            },
        },
    )
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(LORA_DIR / "train_lora.py"),
            "--feedback-source",
            "files",  # 학습 DB 를 건드리지 않고 사이드카 폴더만
            "--feedback-dir",
            str(tmp_path),
            "--augment-file",
            str(tmp_path / "no_aug.jsonl"),
            "--pseudo-dir",
            str(tmp_path / "pseudo"),
            "--seed-file",
            str(tmp_path / "no_seed.jsonl"),  # 저장소 시드 제외 → 피드백 1건만
            "--output",
            str(out),
            "--name",
            "dry",
            "--dry-run",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    manifest = out / "dry" / "run.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["summary"]["records"] == 1
    assert data["dry_run"] is True


def test_seed_cases_and_selector_label(tmp_path: Path):
    """시드 JSONL → selector 포함 정답 레코드 (서빙 규격과 동일 형식)."""
    from dataset import discover_seed_cases

    seed = tmp_path / "seed.jsonl"
    seed.write_text(
        json.dumps({"prompt": "왼쪽에서 두 번째 사람 지워줘",
                    "parsed_prompt": {"target": ["person"], "effect": "remove_object",
                                      "selector": {"position": "left", "rank": 2, "count": 1}}},
                   ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    records = to_instruction_records(discover_seed_cases(seed), origin="seed")
    assert len(records) == 1
    assert '"effect":"remove_object"' in records[0].response_json
    assert '"selector":{"position":"left","rank":2,"count":1,"attributes":[]}' in records[0].response_json


def test_intensity_defaults_when_prompt_has_no_number(tmp_path: Path):
    """숫자 없는 블러 문장의 강도 20 라벨은 기본 15 로 맞춘다 (의사 라벨 노이즈)."""
    _write_case(tmp_path, "p1", {"vote": "like", "source": "pseudo",
                           "meta": {"prompt": "강아지만 남기고 배경 블러",
                                    "parsed_prompt": {"target": ["dog"], "effect": "blur", "intensity": 20}}})
    _write_case(tmp_path, "p2", {"vote": "like", "source": "pseudo",
                           "meta": {"prompt": "강아지만 남기고 배경 블러 강도 20",
                                    "parsed_prompt": {"target": ["dog"], "effect": "blur", "intensity": 20}}})
    records = to_instruction_records(discover_feedback_cases(tmp_path), origin="pseudo")
    by_prompt = {r.prompt: r.response_json for r in records}
    assert '"intensity":15' in by_prompt["강아지만 남기고 배경 블러"]
    assert '"intensity":20' in by_prompt["강아지만 남기고 배경 블러 강도 20"]


def test_eval_prompts_are_dropped_from_training(tmp_path: Path):
    """평가셋과 같은 문장(공백·대소문자 무시)은 학습 레코드에서 빠진다."""
    from dataset import discover_jsonl_cases, drop_eval_leaks, load_eval_prompts

    eval_file = tmp_path / "eval.jsonl"
    eval_file.write_text(json.dumps({"prompt": "사람만 남기고  배경 블러", "parsed_prompt": {"target": ["person"]}},
                                    ensure_ascii=False) + "\n", encoding="utf-8")
    aug = tmp_path / "aug.jsonl"
    aug.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [
        {"prompt": "사람만 남기고 배경 블러", "parsed_prompt": {"target": ["person"], "effect": "blur"}},
        {"prompt": "버스는 남기고 배경만 블러 처리해 주세요", "parsed_prompt": {"target": ["bus"], "effect": "blur"}},
    ]), encoding="utf-8")
    cases = discover_jsonl_cases(aug, "augment")
    assert {c.source for c in cases} == {"augment"}
    records = to_instruction_records(cases, origin="augment")
    kept, dropped = drop_eval_leaks(records, load_eval_prompts(eval_file))
    assert dropped == 1 and [r.prompt for r in kept] == ["버스는 남기고 배경만 블러 처리해 주세요"]
    assert kept[0].origin == "augment"


def test_retrain_decide_requires_gain_and_no_big_drop():
    """재학습 후보 채택: 전체 맞힌 수가 늘고, 어느 평가셋도 max_drop 보다 더 떨어지지 않아야."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("retrain_lora", REPO_ROOT / "scripts" / "retrain_lora.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["retrain_lora"] = mod  # dataclass 가 모듈을 찾을 수 있게
    spec.loader.exec_module(mod)
    S = mod.Score
    base = {"eval": S(35, 40), "eval_ext": S(47, 56)}
    assert mod.decide({"eval": S(37, 40), "eval_ext": S(46, 56)}, base)[0] is True   # +2, -1 허용
    assert mod.decide({"eval": S(39, 40), "eval_ext": S(44, 56)}, base)[0] is False  # -3 하락
    assert mod.decide({"eval": S(35, 40), "eval_ext": S(47, 56)}, base)[0] is False  # 개선 없음
    assert mod.decide({"eval": S(36, 40)}, {"other": S(1, 1)})[0] is False           # 비교 불가

    class C:
        def __init__(self, i):
            self.payload = {"sample_id": i}

    assert [c.payload["sample_id"] for c in mod.new_approved([C("a"), C("b")], {"a"})] == ["b"]
