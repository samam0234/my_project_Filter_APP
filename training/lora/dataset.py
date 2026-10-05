#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""피드백·의사라벨·시드 JSON 을 LoRA instruction 레코드로 변환 (torch 불필요).

의도:
  - data/feedback/*.json (+ 짝 이미지)
  - data/pseudo_labels/*.json (있으면)
  - training/lora/seed/train.jsonl (인스턴스 선택·물체 지우기 시드)
  - 학습 DB learning_samples 중 운영 콘솔에서 승인된 문장 (사용자 교정·좋아요·회원 요청)
  - 승인 문장의 증강 JSONL (augment_prompts.py — 같은 뜻 다른 표현, 자기 일치 검증 통과분)
  → prompt + ParsedPrompt JSON 쌍만 학습에 사용

정답 형식·템플릿은 backend/app/services/prompt_spec.py 를 그대로 쓴다 (서빙과 동일 규격).

비전 마스크 학습은 training/yolo/ 본선. 여기 레코드는
프롬프트 분석기(Causal LM) 도메인 어댑터용이다.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# 서빙 규격 공유: backend/ 를 import 경로에 추가 (pydantic 만 필요, torch 불필요)
_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.prompt_spec import (  # noqa: E402
    ALLOWED_EFFECTS,
    LORA_TEMPLATE,
    LLMError,
    normalize_parsed,
    parsed_to_json,
)


# =============================================================================
# [이미 구현된 구간 · 바이브] 데이터 계약
# -----------------------------------------------------------------------------
# FeedbackService 사이드카와 같은 키를 읽는다.
#   vote, comment, source, image, meta.prompt, meta.parsed_prompt
# =============================================================================

VALID_EFFECTS = frozenset(ALLOWED_EFFECTS)

# 학습·서빙 공용 템플릿 (prompt_spec.LORA_TEMPLATE)
DEFAULT_INSTRUCTION_TEMPLATE = LORA_TEMPLATE


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
    origin: str  # feedback | db | augment | pseudo | seed


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _as_parsed(value: Any) -> Optional[dict[str, Any]]:
    """ParsedPrompt 형태인지 확인 후 정답 dict 로 정규화 (selector 포함).

    서빙과 같은 prompt_spec.normalize_parsed 를 거쳐, 학습 레이블이
    서비스가 실제로 받아들이는 형식과 항상 같게 한다.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict):
        return None
    try:
        return json.loads(parsed_to_json(normalize_parsed(value)))
    except (LLMError, ValueError):
        return None


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


def discover_seed_cases(seed_file: Path) -> list[FeedbackCase]:
    """시드 JSONL ({"prompt", "parsed_prompt"} 한 줄씩) → 케이스. 정답이 확실하므로 like 취급."""
    if not seed_file.is_file():
        return []
    cases: list[FeedbackCase] = []
    for n, line in enumerate(seed_file.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        prompt = payload.get("prompt")
        cases.append(
            FeedbackCase(
                case_id=f"{seed_file.stem}_{n:04d}",
                json_path=seed_file,
                image_path=None,
                vote="like",
                comment=None,
                source="seed",
                prompt=prompt.strip() if isinstance(prompt, str) and prompt.strip() else None,
                parsed_prompt=_as_parsed(payload.get("parsed_prompt")),
                payload=payload,
            )
        )
    return cases


def discover_jsonl_cases(path: Path, source: str) -> list[FeedbackCase]:
    """{"prompt", "parsed_prompt"} JSONL (시드 · 증강 파일) → 케이스. source 로 출처 표시."""
    cases = discover_seed_cases(path)
    for case in cases:
        case.source = source
    return cases


def discover_db_samples(split: Optional[str] = "train", sources: Optional[Iterable[str]] = None) -> list[FeedbackCase]:
    """학습 DB(learning_samples) 중 운영 콘솔에서 **승인된** 문장 샘플.

    split: "train" | "val" | None(전부). 승인 시 id 해시로 고정 배정된 값을 그대로 쓴다.
    정답은 사람이 검수했으므로 like 취급. 접속 정보는 backend Settings(.env) 를 따른다.
    """
    from app.db.learning import learning_session  # noqa: E402 — 학습 DB 가 필요할 때만
    from app.services.learning_review import approved_prompt_samples

    with learning_session() as db:
        rows = approved_prompt_samples(db, list(sources) if sources is not None else None)
    return [
        FeedbackCase(
            case_id=f"db_{r.id}",
            json_path=Path("learning_db"),
            image_path=None,
            vote="like",
            comment=None,
            source=r.source,
            prompt=(r.prompt or "").strip() or None,
            parsed_prompt=_as_parsed(r.answer),
            payload={"split": r.split, "sample_id": r.id},
        )
        for r in rows
        if split is None or r.split == split
    ]


def normalize_prompt(text: str) -> str:
    """누수 검사용 문장 키 (공백·대소문자 무시)."""
    return " ".join(text.lower().split())


def load_eval_prompts(eval_file: Path) -> set[str]:
    """평가셋 문장 키 — 학습 데이터에서 빼서 점수가 부풀지 않게 한다."""
    if not eval_file.is_file():
        return set()
    keys: set[str] = set()
    for line in eval_file.read_text(encoding="utf-8").splitlines():
        try:
            prompt = json.loads(line).get("prompt")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(prompt, str):
            keys.add(normalize_prompt(prompt))
    return keys


def drop_eval_leaks(records: list["InstructionRecord"], eval_prompts: set[str]) -> tuple[list["InstructionRecord"], int]:
    """평가셋과 같은 문장의 레코드를 뺀다. 반환: (남은 레코드, 뺀 수)."""
    kept = [r for r in records if normalize_prompt(r.prompt) not in eval_prompts]
    return kept, len(records) - len(kept)


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


DEFAULT_INTENSITY = 15


def _canonical_intensity(prompt: str, response: dict[str, Any]) -> dict[str, Any]:
    """문장에 숫자가 없으면 intensity 는 기본값 15 (서빙·휴리스틱과 같은 규칙).

    의사 라벨은 숫자 없는 블러 문장에 20 이 붙어 있어, 그대로 학습하면
    "블러 기본 20" 을 배운다. 강도는 프롬프트에서만 오도록 레이블을 맞춘다.
    """
    if re.search(r"\d", prompt) or response.get("intensity") == DEFAULT_INTENSITY:
        return response
    return {**response, "intensity": DEFAULT_INTENSITY}


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
        elif origin in {"pseudo", "seed", "db", "augment"} or source in {"pseudo", "seed"}:
            response = case.parsed_prompt
        elif vote == "dislike":
            response = comment_as_parsed(case.comment)
        elif vote == "like":
            response = case.parsed_prompt
        else:
            response = case.parsed_prompt

        if response is None:
            continue
        response = _canonical_intensity(prompt, response)
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
        elif isinstance(value, (list, tuple)):
            out[key] = [str(v) if isinstance(v, Path) else v for v in value]
        else:
            out[key] = value
    return out


def record_as_dict(record: InstructionRecord) -> dict[str, Any]:
    return asdict(record)
