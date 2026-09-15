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
            "--feedback-dir",
            str(tmp_path),
            "--pseudo-dir",
            str(tmp_path / "pseudo"),
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
