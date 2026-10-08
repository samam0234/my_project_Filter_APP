#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 문장 해석(LLM)이 "지정한 대상만" 정확히 뽑는가 — 대상이 틀리면 뒤 단계가 아무리 좋아도 엉뚱한 것이 남는다.

평가셋 = 기존 eval.jsonl(40) + eval_ext.jsonl(56) + eval_distractor.jsonl(47, **다른 물체·사람이 함께 언급되는 문장**).
파서마다 N 번 반복해(LLM 은 같은 문장에 다른 답을 낼 수 있다) 라운드로 채점한다.

지표 (문장 단위)
  exact        모든 필드 일치
  target_ok    대상 목록이 정확히 같다
  extra        예측 대상이 정답의 **초과**를 포함한다 (정답 ⊂ 예측, 더 많음)  ← "언급 안 된 것까지 대상으로" 의 직접 원인
  missing      정답 대상 중 일부가 빠졌다
  wrong        초과도 누락도 아닌 다른 대상 (예: dog → cat)
  effect_ok / selector_ok  효과 · 위치/순번/개수가 맞다
  stability    같은 문장을 N 번 물었을 때 같은 답이 나온 비율
  vote         N 번 답의 다수결(대상 · 효과 · 선택자 조합)로 채점한 결과 — 여러 번 묻는 자기일관성이 얼마나 도움이 되나

파서
  heuristic        LLM 없이 키워드 파서 (backend/app/workflows/nodes.parse_prompt_heuristic)
  ollama           서비스 LLM, RAG 없음
  ollama_rag       서비스와 같은 RAG (학습 DB 의 승인된 샘플) — 학습 DB 가 비어 있으면 ollama 와 같다
  ollama_rag_seed  RAG 지식 베이스 = 시드 train.jsonl (800문장). 평가 문장은 빼서 정답 누수를 막는다
  ollama_rag_new   위 + train_distractor.jsonl (방해물 학습 문장 — "새 학습 내용" 이 RAG 로 바로 반영되는지)

실행: python scripts/experiments/parse_rounds.py --parsers ollama,ollama_rag_seed,ollama_rag_new --repeat 3 --out docs/vaildates/parse_rounds_20261008.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/lora"))
sys.path.insert(0, str(ROOT / "backend"))

from eval_parser import _flatten, load_eval, make_parsers  # noqa: E402

SEEDS = ROOT / "training/lora/seed"
SETS = {"eval": "eval.jsonl", "ext": "eval_ext.jsonl", "distractor": "eval_distractor.jsonl", "holdout": "eval_holdout.jsonl"}


def make_rag_parser(kind: str, rows):
    """시드(+방해물 학습 문장) 지식 베이스로 RAG 를 붙인 Ollama 파서. 평가 문장은 지식 베이스에서 뺀다."""
    from app.core.config import Settings
    from app.services.prompt_llm import parse_prompt_llm
    from app.services.prompt_rag import ExampleIndex, format_examples, load_examples
    from app.services.prompt_spec import parsed_to_json

    s = Settings.model_validate({"LLM_PROVIDER": "ollama", "LLM_TIMEOUT_SECONDS": 120})
    examples = load_examples(SEEDS / "train.jsonl", None)
    if kind == "new":
        examples += load_examples(SEEDS / "train_distractor.jsonl", None)
    held_out = {" ".join(r["prompt"].lower().split()) for r in rows}
    examples = [e for e in examples if " ".join(e.prompt.lower().split()) not in held_out]
    index = ExampleIndex(examples)
    print(f"(ollama_rag_{kind} 지식 베이스 {len(examples)}건)")

    def _parse(text, s=s, index=index):
        hits = index.search(text, k=s.prompt_rag_top_k, min_score=s.prompt_rag_min_score)
        return json.loads(parsed_to_json(parse_prompt_llm(text, s, examples=format_examples(hits))))

    return _parse


def classify(pred: dict | None, gold: dict) -> dict:
    if pred is None:
        return {"valid": False, "exact": False, "target_ok": False, "kind": "invalid", "effect_ok": False, "selector_ok": False}
    p, g = _flatten(pred), _flatten(gold)
    pt, gt = set(p["target"]), set(g["target"])
    if pt == gt:
        kind = "ok"
    elif gt < pt:
        kind = "extra"
    elif pt < gt:
        kind = "missing"
    else:
        kind = "wrong"
    sel = all(p[k] == g[k] for k in ("position", "rank", "count"))
    return {
        "valid": True,
        "exact": all(p[k] == g[k] for k in g),
        "target_ok": kind == "ok",
        "kind": kind,
        "effect_ok": p["effect"] == g["effect"],
        "selector_ok": sel,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parsers", default="ollama,ollama_rag")
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--sets", default="eval,ext,distractor")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = []
    for name in args.sets.split(","):
        for r in load_eval(SEEDS / SETS[name]):
            r["set"] = name
            rows.append(r)
    if args.limit:
        rows = rows[: args.limit]
    args.eval_rows = rows
    args.adapter, args.base_model = None, None
    print(f"평가 문장 {len(rows)}개 ({Counter(r['set'] for r in rows)}) × 반복 {args.repeat}")
    names = args.parsers.split(",")
    custom = {n: make_rag_parser(n.rsplit("_", 1)[1], rows) for n in names if n in ("ollama_rag_seed", "ollama_rag_new")}
    parsers = make_parsers([n for n in names if n not in custom], args) | custom
    parsers = {n: parsers[n] for n in names}

    report = {}
    for pname, parse in parsers.items():
        runs = 1 if pname == "heuristic" else args.repeat
        answers = {i: [] for i in range(len(rows))}
        for rep in range(runs):
            stats = Counter()
            per_set = {s: Counter() for s in SETS}
            t0 = time.time()
            for i, row in enumerate(rows):
                try:
                    pred = parse(row["prompt"])
                except Exception:
                    pred = None
                answers[i].append(json.dumps(pred, ensure_ascii=False, sort_keys=True) if pred else None)
                c = classify(pred, row["gold"])
                for tgt in (stats, per_set[row["set"]]):
                    tgt["n"] += 1
                    for k in ("valid", "exact", "target_ok", "effect_ok", "selector_ok"):
                        tgt[k] += bool(c[k])
                    tgt[c["kind"]] += 1
            n = stats["n"]
            line = " ".join(f"{k}={stats[k] / n:.3f}" for k in ("exact", "target_ok", "effect_ok", "selector_ok"))
            line += f" | 초과 {stats['extra']} 누락 {stats['missing']} 다른대상 {stats['wrong']} 무효 {stats['invalid']}"
            d = per_set["distractor"]
            line += f" | 방해물 문장 target_ok={d['target_ok'] / max(d['n'], 1):.3f} 초과 {d['extra']}"
            print(f"{pname:11} 라운드{rep + 1} {time.time() - t0:5.0f}s {line}", flush=True)
            report.setdefault(pname, []).append({
                "round": rep + 1, "seconds": round(time.time() - t0, 1),
                "overall": {k: round(stats[k] / n, 4) for k in ("exact", "target_ok", "effect_ok", "selector_ok")} | {
                    "extra": stats["extra"], "missing": stats["missing"], "wrong": stats["wrong"], "invalid": stats["invalid"], "n": n},
                "by_set": {s: {"n": c["n"], "target_ok": round(c["target_ok"] / max(c["n"], 1), 4), "exact": round(c["exact"] / max(c["n"], 1), 4),
                               "extra": c["extra"], "missing": c["missing"], "wrong": c["wrong"]} for s, c in per_set.items() if c["n"]},
            })
        # 다수결: 같은 문장의 N 번 답 중 가장 많이 나온 (대상, 효과, 선택자) 조합을 고른다 (동률이면 먼저 나온 것)
        keyf = lambda p_: json.dumps({k: _flatten(p_)[k] for k in ("target", "effect", "position", "rank", "count")}, sort_keys=True)  # noqa: E731
        if runs >= 3:
            vstats, vset = Counter(), {s_: Counter() for s_ in SETS}
            for i, row in enumerate(rows):
                parsed = [json.loads(a) for a in answers[i] if a]
                pick = None
                if parsed:
                    top = Counter(keyf(p_) for p_ in parsed).most_common(1)[0][0]
                    pick = next(p_ for p_ in parsed if keyf(p_) == top)
                c = classify(pick, row["gold"])
                for tgt in (vstats, vset[row["set"]]):
                    tgt["n"] += 1
                    tgt[c["kind"]] += 1
                    tgt["target_ok"] += bool(c["target_ok"])
                    tgt["effect_ok"] += bool(c["effect_ok"])
            n = vstats["n"]
            d = vset["distractor"]
            print(f"{pname:11} 다수결({runs}회) target_ok={vstats['target_ok'] / n:.3f} effect_ok={vstats['effect_ok'] / n:.3f} "
                  f"초과 {vstats['extra']} 누락 {vstats['missing']} 다른대상 {vstats['wrong']} | 방해물 문장 target_ok={d['target_ok'] / max(d['n'], 1):.3f}", flush=True)
            report[pname + "_vote"] = {"target_ok": round(vstats["target_ok"] / n, 4), "effect_ok": round(vstats["effect_ok"] / n, 4),
                                       "extra": vstats["extra"], "missing": vstats["missing"], "wrong": vstats["wrong"],
                                       "distractor_target_ok": round(d["target_ok"] / max(d["n"], 1), 4)}
        report[pname + "_answers"] = [{"prompt": rows[i]["prompt"], "set": rows[i]["set"],
                                       "gold": _flatten(rows[i]["gold"])["target"], "answers": answers[i]} for i in range(len(rows))]
        same = sum(1 for v in answers.values() if len(set(v)) == 1)
        report[pname + "_stability"] = round(same / len(rows), 4)
        print(f"{pname:11} 안정성(같은 문장 {runs}번 같은 답) {same}/{len(rows)} = {same / len(rows):.3f}")
        # 자주 틀리는 문장 (모든 반복에서 대상이 틀린 것)
        bad = []
        for i, row in enumerate(rows):
            if all(a is None or classify(json.loads(a), row["gold"])["kind"] != "ok" for a in answers[i]):
                bad.append({"prompt": row["prompt"], "gold": _flatten(row["gold"])["target"],
                            "pred": sorted({tuple(_flatten(json.loads(a))["target"]) for a in answers[i] if a})[:2] if any(answers[i]) else None,
                            "set": row["set"]})
        report[pname + "_always_wrong"] = bad
        print(f"{pname:11} 반복 모두 대상이 틀린 문장 {len(bad)}개")
        for b in bad[:12]:
            print("   -", b["prompt"], "| 정답", b["gold"], "| 예측", b["pred"])
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
