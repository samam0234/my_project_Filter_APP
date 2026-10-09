#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 문장 해석기 비교 — 지금 서비스(Ollama + 키워드 파서 체인) vs LoRA vs 둘을 섞은 체인.

LoRA 는 greedy 생성이라 같은 문장에 늘 같은 답을 낸다 → 지금 체인에 LoRA 만 넣으면 다시 물어도 같은 답이라
투표에서 항상 LoRA 가 이긴다 (체인 + LoRA = LoRA 단독). 그래서 비교하는 것은:

  heuristic     키워드 파서만 (LLM 없음)
  chain_ollama  지금 서비스 기본 — Ollama 1번, 키워드 파서와 대상이 다르면 최대 3번까지 + 키워드 파서 한 표
  lora          LoRA 단독
  chain_hybrid  LoRA 먼저, 키워드 파서와 대상이 다르면 Ollama 한 번 더 → LoRA · Ollama · 키워드 파서 셋이 투표
                (셋이 다 다르면 LoRA). Ollama 는 의견이 갈릴 때만 부른다

RAG 예시는 붙이지 않는다 (모든 파서 같은 조건). 시간은 문장당 평균 (모델 로드 제외).
실행: python scripts/experiments/parser_compare.py --out docs/vaildates/parser_compare_20261009.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/lora"))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts/experiments"))

from eval_parser import load_eval  # noqa: E402
from parse_rounds import classify  # noqa: E402

SEEDS = ROOT / "training/lora/seed"
SETS = {"eval": "eval.jsonl", "ext": "eval_ext.jsonl", "distractor": "eval_distractor.jsonl",
        "holdout": "eval_holdout.jsonl", "fresh": "eval_fresh.jsonl", "fresh2": "eval_fresh2.jsonl",
        "fresh3": "eval_fresh3.jsonl"}


def make(names: list[str], adapter: str | None):
    from app.core.config import Settings
    from app.services.prompt_chain import parse_prompt_chain
    from app.services.prompt_llm import parse_prompt_llm
    from app.services.prompt_spec import parsed_to_json
    from app.workflows.nodes import parse_prompt_heuristic

    to_dict = lambda p: json.loads(parsed_to_json(p))  # noqa: E731
    ollama = Settings.model_validate({"LLM_PROVIDER": "ollama", "LLM_FALLBACK": "none", "LLM_TIMEOUT_SECONDS": 120,
                                      "PROMPT_CHAIN": "langchain", "PROMPT_VOTES": 3})
    lora_kw = {"LLM_PROVIDER": "lora", "LLM_FALLBACK": "none",
               "LORA_BASE_MODEL": str(ROOT / "training" / "models" / "qwen2.5-1.5b-instruct")}
    if adapter:
        lora_kw["LORA_ADAPTER_PATH"] = adapter
    lora = Settings.model_validate(lora_kw)
    hybrid = ollama.model_copy(update={"prompt_votes": 2})
    calls: dict[str, int] = {}

    def counted(name, fn):
        def run(*a, **k):
            calls[name] = calls.get(name, 0) + 1
            return fn(*a, **k)
        return run

    ask_ollama = counted("ollama", lambda t, s, e="": parse_prompt_llm(t, ollama, e))
    ask_lora = counted("lora", lambda t, s, e="": parse_prompt_llm(t, lora, e))

    def hybrid_ask():
        n = {"i": 0}

        def ask(t, s, e=""):
            n["i"] += 1
            return ask_lora(t, s, e) if n["i"] == 1 else ask_ollama(t, s, e)
        return ask

    out = {}
    for name in names:
        if name == "heuristic":
            out[name] = lambda t: to_dict(parse_prompt_heuristic(t))
        elif name == "chain_ollama":
            out[name] = lambda t: to_dict(parse_prompt_chain(t, ollama, ask=ask_ollama))
        elif name == "lora":
            out[name] = lambda t: to_dict(ask_lora(t, lora))
        elif name == "chain_hybrid":
            out[name] = lambda t: to_dict(parse_prompt_chain(t, hybrid, ask=hybrid_ask()))
    return out, calls


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parsers", default="heuristic,lora,chain_hybrid,chain_ollama")
    ap.add_argument("--sets", default=",".join(SETS))
    ap.add_argument("--adapter", default=None, help="LoRA 어댑터 (기본: 설정의 backend/models/lora)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    parsers, calls = make(args.parsers.split(","), args.adapter)
    if "lora" in parsers or "chain_hybrid" in parsers:
        parsers.get("lora", parsers.get("chain_hybrid"))("사람만 남겨줘")  # 모델 로드 (시간에서 뺀다)
    report = {"sets": {}, "parsers": list(parsers)}
    for set_name in args.sets.split(","):
        rows = load_eval(SEEDS / SETS[set_name])
        res = {}
        for pname, fn in parsers.items():
            before = dict(calls)
            t0 = time.perf_counter()
            items = []
            for r in rows:
                try:
                    pred = fn(r["prompt"])
                except Exception as exc:  # noqa: BLE001 — 실패도 오답으로 센다
                    pred = None
                    print(f"  ! {pname} 실패: {r['prompt']} ({exc})")
                c = classify(pred, r["gold"])
                items.append({"prompt": r["prompt"], "pred": pred, **c})
            sec = (time.perf_counter() - t0) / len(rows)
            res[pname] = {
                "n": len(rows),
                "exact": sum(i["exact"] for i in items) / len(rows),
                "target": sum(i["target_ok"] for i in items) / len(rows),
                "extra": sum(i["kind"] == "extra" for i in items),
                "sec": sec,
                "calls": {k: calls.get(k, 0) - before.get(k, 0) for k in calls},
                "misses": [i for i in items if not i["exact"]],
            }
            print(f"{set_name:10} {pname:13} 전 항목 {res[pname]['exact']:.3f} 대상 {res[pname]['target']:.3f} "
                  f"초과 {res[pname]['extra']} {sec:.2f}초/문장 호출 {res[pname]['calls']}", flush=True)
        report["sets"][set_name] = res
    total = {}
    for pname in parsers:
        n = sum(report["sets"][s][pname]["n"] for s in report["sets"])
        total[pname] = {
            "n": n,
            "exact": sum(report["sets"][s][pname]["exact"] * report["sets"][s][pname]["n"] for s in report["sets"]) / n,
            "target": sum(report["sets"][s][pname]["target"] * report["sets"][s][pname]["n"] for s in report["sets"]) / n,
            "sec": sum(report["sets"][s][pname]["sec"] * report["sets"][s][pname]["n"] for s in report["sets"]) / n,
        }
        print(f"전체 {pname:13} n={n} 전 항목 {total[pname]['exact']:.3f} 대상 {total[pname]['target']:.3f} {total[pname]['sec']:.2f}초/문장")
    report["total"] = total
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
