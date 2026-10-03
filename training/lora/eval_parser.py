#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""프롬프트 분석기 평가: 같은 평가셋으로 파서들을 나란히 채점한다.

파서:
  heuristic : backend 키워드 파서 (LLM 실패 시 fallback)
  ollama    : 서비스 LLM (SYSTEM_PROMPT few-shot, 기본 gemma4:e4b)
  ollama_rag: ollama + RAG 예시 (services/prompt_rag, 평가 문장은 지식 베이스에서 제외)
  base      : LoRA 없이 베이스 모델 + LORA_TEMPLATE (어댑터 효과 비교용)
  lora      : 베이스 + 학습한 어댑터 (서빙 services/prompt_lora 와 같은 코드)

사용:
  python training/lora/eval_parser.py --adapter training/outputs/lora/instance_v1/adapter
  python training/lora/eval_parser.py --parsers heuristic,ollama
결과: 표 출력 + --report JSON (틀린 샘플 포함)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

_LORA_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _LORA_DIR.parents[1]
_BACKEND = _REPO_ROOT / "backend"
for p in (str(_LORA_DIR), str(_BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.instance_selector import parse_attribute  # noqa: E402
from app.services.prompt_spec import normalize_parsed, parsed_to_json  # noqa: E402

FIELDS = ("target", "effect", "intensity", "crop", "position", "rank", "count", "attributes")


def load_eval(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            row["gold"] = json.loads(parsed_to_json(normalize_parsed(row["parsed_prompt"])))
            rows.append(row)
    return rows


def _flatten(parsed: dict[str, Any]) -> dict[str, Any]:
    sel = parsed.get("selector") or {}
    return {
        "target": sorted(parsed.get("target") or []),
        "effect": parsed.get("effect"),
        "intensity": parsed.get("intensity"),
        "crop": parsed.get("crop"),
        "position": sel.get("position"),
        "rank": sel.get("rank"),
        # position 이 있으면 count 기본 1 로 동작하므로 null 과 1 을 같게 본다
        "count": sel.get("count") or (1 if sel.get("position") else None),
        # 문자열이 아니라 선택기가 해석하는 (색, 부위) 로 비교:
        # "fluorescent vest" == "neon yellow vest", "black" == "black car" (사물은 부위 없음)
        "attributes": sorted(
            {tuple(str(x) for x in parse_attribute(a)) for a in sel.get("attributes") or []}
        ),
    }


def score(pred: Optional[dict[str, Any]], gold: dict[str, Any]) -> dict[str, bool]:
    g = _flatten(gold)
    if pred is None:
        return {f: False for f in FIELDS} | {"exact": False, "valid": False}
    p = _flatten(pred)
    out = {f: p[f] == g[f] for f in FIELDS}
    out["exact"] = all(out.values())
    out["valid"] = True
    return out


def make_parsers(names: list[str], args: argparse.Namespace) -> dict[str, Callable[[str], dict]]:
    parsers: dict[str, Callable[[str], dict]] = {}
    for name in names:
        if name == "heuristic":
            from app.workflows.nodes import parse_prompt_heuristic

            parsers[name] = lambda t: json.loads(parsed_to_json(parse_prompt_heuristic(t)))
        elif name == "ollama":
            from app.core.config import Settings
            from app.services.prompt_llm import parse_prompt_llm

            s = Settings.model_validate({"LLM_PROVIDER": "ollama", "LLM_TIMEOUT_SECONDS": 120})
            parsers[name] = lambda t, s=s: json.loads(parsed_to_json(parse_prompt_llm(t, s)))
        elif name == "ollama_rag":
            # 서비스와 같은 RAG(PROMPT_RAG_SOURCES — 기본 사용자 교정·좋아요)로 예시를 붙여 Ollama 호출.
            # 평가 문장과 같은 예시는 지식 베이스에서 빼서 정답 누수를 막는다.
            from app.core.config import Settings
            from app.services.prompt_llm import parse_prompt_llm
            from app.services.prompt_rag import ExampleIndex, PromptRAG, format_examples

            s = Settings.model_validate({"LLM_PROVIDER": "ollama", "LLM_TIMEOUT_SECONDS": 120})
            held_out = {" ".join(r["prompt"].lower().split()) for r in args.eval_rows}
            base = PromptRAG(s).index()
            index = ExampleIndex(
                [e for e in base.examples if " ".join(e.prompt.lower().split()) not in held_out]
            )
            print(f"(ollama_rag 지식 베이스 {len(index.examples)}건, 평가 문장 {len(base.examples) - len(index.examples)}건 제외)")

            def _rag(t, s=s, index=index):
                hits = index.search(t, k=s.prompt_rag_top_k, min_score=s.prompt_rag_min_score)
                return json.loads(parsed_to_json(parse_prompt_llm(t, s, examples=format_examples(hits))))

            parsers[name] = _rag
        elif name in {"base", "lora"}:
            from app.services.prompt_lora import LoraPromptParser

            adapter = args.adapter if name == "lora" else None
            if name == "lora" and adapter is None:
                raise SystemExit("--adapter 를 주세요 (lora 평가)")
            engine = LoraPromptParser(args.base_model, adapter)
            parsers[name] = lambda t, e=engine: json.loads(parsed_to_json(e.parse(t)))
        else:
            raise SystemExit(f"알 수 없는 파서: {name}")
    return parsers


def evaluate(rows, parse: Callable[[str], dict]) -> tuple[dict[str, float], list[dict], float]:
    totals = {f: 0 for f in (*FIELDS, "exact", "valid")}
    misses = []
    started = time.time()
    for row in rows:
        try:
            pred = parse(row["prompt"])
        except Exception as exc:  # 파싱 실패 = 오답
            pred = None
            err = str(exc)[:200]
        else:
            err = None
        sc = score(pred, row["gold"])
        for k, v in sc.items():
            totals[k] += int(v)
        if not sc["exact"]:
            misses.append({"prompt": row["prompt"], "gold": row["gold"], "pred": pred, "error": err,
                           "wrong": [f for f in FIELDS if not sc[f]]})
    n = max(1, len(rows))
    return {k: v / n for k, v in totals.items()}, misses, (time.time() - started) / n


def main() -> None:
    ap = argparse.ArgumentParser(description="프롬프트 분석기 평가")
    ap.add_argument("--eval-file", type=Path, default=_LORA_DIR / "seed" / "eval.jsonl")
    ap.add_argument("--parsers", default="heuristic,ollama,base,lora")
    ap.add_argument("--base-model", type=Path,
                    default=_REPO_ROOT / "training" / "models" / "qwen2.5-1.5b-instruct")
    ap.add_argument("--adapter", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None, help="결과 JSON 저장 경로")
    args = ap.parse_args()

    rows = load_eval(args.eval_file)
    args.eval_rows = rows
    names = [n.strip() for n in args.parsers.split(",") if n.strip()]
    if "lora" in names and args.adapter is None:
        names.remove("lora")
        print("(--adapter 없음 → lora 평가 생략)")
    parsers = make_parsers(names, args)

    report: dict[str, Any] = {"eval_file": str(args.eval_file), "n": len(rows), "results": {}}
    cols = ("exact", "target", "effect", "position", "rank", "count", "attributes", "valid")
    print(f"\n평가셋 {args.eval_file.name}: {len(rows)}건")
    print(f"{'parser':<10}" + "".join(f"{c:>11}" for c in cols) + f"{'sec/건':>9}")
    for name, parse in parsers.items():
        acc, misses, sec = evaluate(rows, parse)
        print(f"{name:<10}" + "".join(f"{acc[c]*100:>10.1f}%" for c in cols) + f"{sec:>9.2f}")
        report["results"][name] = {"accuracy": acc, "sec_per_item": sec, "misses": misses}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nreport → {args.report}")


if __name__ == "__main__":
    main()
