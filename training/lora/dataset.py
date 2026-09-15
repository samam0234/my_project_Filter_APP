#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""피드백·의사라벨 JSON 을 LoRA instruction 레코드로 변환 (torch 불필요).

의도:
  - data/feedback/*.json (+ 짝 이미지)
  - data/pseudo_labels/*.json (있으면)
  → prompt + ParsedPrompt JSON 쌍만 학습에 사용

비전 마스크 학습은 training/yolo/ 본선. 여기 레코드는
프롬프트 분석기(Causal LM) 도메인 어댑터용이다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


# =============================================================================
# [이미 구현된 구간 · 바이브] 데이터 계약
# -----------------------------------------------------------------------------
# FeedbackService 사이드카와 같은 키를 읽는다.
#   vote, comment, source, image, meta.prompt, meta.parsed_prompt
# =============================================================================

VALID_EFFECTS = frozenset({"remove_bg", "blur", "crop", "none"})

DEFAULT_INSTRUCTION_TEMPLATE = """### 지시
컷앤킵 이미지 필터 프롬프트를 ParsedPrompt JSON 한 줄로 변환하세요.
스키마: {{"target":["class"],"effect":"remove_bg|blur|crop|none","intensity":0-100,"crop":true|false}}
target 은 YOLO 클래스 소문자와 같아야 합니다.

### 프롬프트
{prompt}

### 응답
{response}
"""


@dataclass
class FeedbackCase:
    """사이드카 한 건."""

    case_id: str
    json_path: Path
    image_path: Optional[Path]
    vote: str
    comment: Optional[str]
    source: str
    prompt: Optional[str]
    parsed_prompt: Optional[dict[str, Any]]
    payload: dict[str, Any] = field(repr=False)


@dataclass
class InstructionRecord:
    """Causal LM 학습 한 샘플."""

    case_id: str
    text: str
    prompt: str
    response_json: str
    vote: str
    source: str
    origin: str  # feedback | pseudo


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _as_parsed(value: Any) -> Optional[dict[str, Any]]:
    """ParsedPrompt 형태인지 느슨히 확인 후 dict 로 정규화."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict):
        return None
    target = value.get("target")
    effect = value.get("effect")
    if not isinstance(target, list) or not target:
        return None
    if not all(isinstance(t, str) and t.strip() for t in target):
        return None
    if effect is not None and str(effect) not in VALID_EFFECTS:
        return None
    intensity = value.get("intensity", 15)
    try:
        intensity_i = int(intensity)
    except (TypeError, ValueError):
        intensity_i = 15
    intensity_i = max(0, min(100, intensity_i))
    crop = bool(value.get("crop", False))
    return {
        "target": [str(t).strip().lower() for t in target],
        "effect": str(effect or "remove_bg"),
        "intensity": intensity_i,
        "crop": crop,
    }


def _prompt_from_payload(payload: dict[str, Any]) -> Optional[str]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    raw = payload.get("prompt") or meta.get("prompt")
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text or None


def _parsed_from_payload(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    return _as_parsed(payload.get("parsed_prompt") or meta.get("parsed_prompt"))


def _sidecar_image(json_path: Path, payload: dict[str, Any]) -> Optional[Path]:
    name = payload.get("image")
    if isinstance(name, str) and name.strip():
        p = json_path.parent / name
        if p.is_file():
            return p
    stem = json_path.with_suffix("")
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = Path(str(stem) + ext)
        if p.is_file():
            return p
    return None


def discover_feedback_cases(feedback_dir: Path) -> list[FeedbackCase]:
    """data/feedback/*.json 을 읽어 케이스 목록으로 만든다. 깨진 JSON 은 건너뛴다."""
    if not feedback_dir.is_dir():
        return []
    cases: list[FeedbackCase] = []
    for json_path in sorted(feedback_dir.glob("*.json")):
        payload = _read_json(json_path)
        if payload is None:
            continue
        case_id = str(payload.get("case_id") or json_path.stem)
        vote = str(payload.get("vote") or "").strip().lower()
        comment = payload.get("comment")
        if comment is not None:
            comment = str(comment)
        source = str(payload.get("source") or (payload.get("meta") or {}).get("source") or "user")
        cases.append(
            FeedbackCase(
                case_id=case_id,
                json_path=json_path,
                image_path=_sidecar_image(json_path, payload),
                vote=vote,
                comment=comment,
                source=source,
                prompt=_prompt_from_payload(payload),
                parsed_prompt=_parsed_from_payload(payload),
                payload=payload,
            )
        )
    return cases


def discover_pseudo_cases(pseudo_dir: Path) -> list[FeedbackCase]:
    """data/pseudo_labels/*.json — 피드백과 같은 키를 재사용한다."""
    cases = discover_feedback_cases(pseudo_dir)
    for case in cases:
        if not case.source or case.source == "user":
            case.source = "pseudo"
        if not case.vote:
            case.vote = "like"
    return cases


def comment_as_parsed(comment: Optional[str]) -> Optional[dict[str, Any]]:
    """dislike 코멘트가 ParsedPrompt JSON 이면 정답으로 쓴다."""
    if not comment or not comment.strip():
        return None
    text = comment.strip()
    # 앞뒤 설명 문장 없이 JSON 객체만 있는 경우
    if not (text.startswith("{") and text.endswith("}")):
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        text = text[start : end + 1]
    return _as_parsed(text)


def to_instruction_records(
    cases: Iterable[FeedbackCase],
    *,
    template: str = DEFAULT_INSTRUCTION_TEMPLATE,
    include_pipeline_failure: bool = True,
    origin: str = "feedback",
) -> list[InstructionRecord]:
    """학습에 쓸 수 있는 (prompt, ParsedPrompt) 쌍만 남긴다.

    정책 (기본):
      - pipeline_failure: source 우선 (vote 가 dislike 여도 약한 정답)
      - pseudo: parsed_prompt
      - like: prompt + parsed_prompt
      - dislike: 코멘트가 ParsedPrompt JSON 일 때만 (시스템 출력은 오답)
    """
    records: list[InstructionRecord] = []
    for case in cases:
        prompt = case.prompt
        if not prompt:
            continue
        response: Optional[dict[str, Any]] = None
        vote = case.vote
        source = case.source

        # pipeline_failure 는 vote=dislike 로 저장되므로 source 를 먼저 본다.
        if source == "pipeline_failure":
            if include_pipeline_failure:
                response = case.parsed_prompt
        elif origin == "pseudo" or source == "pseudo":
            response = case.parsed_prompt
        elif vote == "dislike":
            response = comment_as_parsed(case.comment)
        elif vote == "like":
            response = case.parsed_prompt
        else:
            response = case.parsed_prompt

        if response is None:
            continue
        response_json = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
        text = template.format(prompt=prompt, response=response_json)
        records.append(
            InstructionRecord(
                case_id=case.case_id,
                text=text,
                prompt=prompt,
                response_json=response_json,
                vote=vote or "unknown",
                source=source,
                origin=origin,
            )
        )
    return records


def summarize_cases(cases: list[FeedbackCase], records: list[InstructionRecord]) -> dict[str, Any]:
    """dry-run / run.json 용 집계."""
    votes: dict[str, int] = {}
    skipped = 0
    with_image = 0
    for case in cases:
        votes[case.vote or "unknown"] = votes.get(case.vote or "unknown", 0) + 1
        if case.image_path is not None:
            with_image += 1
    skipped = max(0, len(cases) - len(records))
    return {
        "cases": len(cases),
        "records": len(records),
        "skipped": skipped,
        "with_image": with_image,
        "votes": votes,
    }


def write_run_manifest(
    path: Path,
    *,
    args: dict[str, Any],
    summary: dict[str, Any],
    records: list[InstructionRecord],
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """학습/dry-run 메타를 JSON 으로 남긴다. 가중치는 넣지 않는다."""
    payload: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "args": args,
        "summary": summary,
        "samples": [
            {
                "case_id": r.case_id,
                "vote": r.vote,
                "source": r.source,
                "origin": r.origin,
                "prompt": r.prompt,
                "response_json": r.response_json,
            }
            for r in records
        ],
    }
    if extra:
        payload.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def args_to_jsonable(args: Any) -> dict[str, Any]:
    """argparse.Namespace → JSON 가능 dict."""
    raw = vars(args) if hasattr(args, "__dict__") else dict(args)
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, Path):
            out[key] = str(value)
        else:
            out[key] = value
    return out


def record_as_dict(record: InstructionRecord) -> dict[str, Any]:
    return asdict(record)
