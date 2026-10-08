#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사용자 데이터 재학습 루프 — 승인 문장이 충분히 쌓이면 LoRA 를 다시 학습하고 배포본과 비교한다.

흐름
  1. 학습 DB 의 승인된 문장(train split) 중 지난 재학습 이후 새로 승인된 수를 센다
  2. 기준(--min-new, 기본 LORA_RETRAIN_MIN_NEW=200) 미만이면 "대기" 만 알리고 끝 (--force 로 강제)
  3. 증강(training/lora/augment_prompts.py) → 학습(scripts/fine_tune_lora.py) → 평가(eval_parser)
     평가셋: seed/eval.jsonl(40) · eval_ext.jsonl(56) · eval_distractor.jsonl(47) · eval_holdout.jsonl(40) · 승인 val split(있으면)
  4. 지금 배포된 어댑터(backend/models/lora)와 같은 평가셋으로 비교 → 보고서 md
  5. --deploy 이고 후보가 이기면 배포본을 backend/models/lora_prev_<시각> 로 옮기고 교체 (백엔드 재시작 필요)

판정 (decide): 전체 맞힌 수가 배포본보다 많고, 어느 평가셋에서도 --max-drop(기본 1문항)보다 더 떨어지지 않을 때만 채택.
평가셋이 작아 1~2문항은 재학습만으로도 흔들린다 — 그래서 "더 많이 맞힘 + 크게 떨어진 곳 없음" 둘 다 요구한다.

실행 (저장소 루트, training venv, Ollama 실행 중):
  python scripts/retrain_lora.py                 # 기준 확인만 (모자라면 대기)
  python scripts/retrain_lora.py --force         # 기준 무시하고 한 바퀴 (점검용)
  python scripts/retrain_lora.py --deploy        # 이기면 배포본 교체
상태 파일: training/outputs/lora/retrain_state.json (마지막으로 학습에 쓴 승인 샘플 id)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LORA = ROOT / "training" / "lora"
OUT = ROOT / "training" / "outputs" / "lora"
STATE = OUT / "retrain_state.json"
DEPLOYED = ROOT / "backend" / "models" / "lora"
EVAL_SETS = {
    "eval": LORA / "seed" / "eval.jsonl",
    "eval_ext": LORA / "seed" / "eval_ext.jsonl",
    # 지정하지 않은 물체·사람이 같이 언급되는 문장 — 여기서 악화되면 채택하지 않는다 (docs/vaildates/leak-diagnosis-20261008.md)
    "eval_distractor": LORA / "seed" / "eval_distractor.jsonl",
    "eval_holdout": LORA / "seed" / "eval_holdout.jsonl",
}


@dataclass
class Score:
    correct: int
    total: int

    @property
    def rate(self) -> float:
        return self.correct / self.total if self.total else 0.0


def decide(candidate: dict[str, Score], deployed: dict[str, Score], max_drop: int = 1) -> tuple[bool, str]:
    """후보 채택 여부와 이유. 평가셋 이름이 같은 것끼리만 비교한다."""
    names = sorted(set(candidate) & set(deployed))
    if not names:
        return False, "비교할 평가셋이 없음"
    gain = sum(candidate[n].correct - deployed[n].correct for n in names)
    drops = {n: deployed[n].correct - candidate[n].correct for n in names}
    worst = max(drops.items(), key=lambda kv: kv[1])
    if worst[1] > max_drop:
        return False, f"{worst[0]} 에서 {worst[1]}문항 하락 (허용 {max_drop})"
    if gain <= 0:
        return False, f"전체 맞힌 수 차이 {gain:+d} — 개선 없음"
    return True, f"전체 {gain:+d}문항, 최대 하락 {max(0, worst[1])}문항"


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"trained_ids": [], "runs": []}


def new_approved(samples: list, trained_ids: set[str]) -> list:
    return [s for s in samples if s.payload.get("sample_id") not in trained_ids]


def run(cmd: list[str], log: Path) -> None:
    print("→", " ".join(str(c) for c in cmd[1:]), flush=True)
    with log.open("a", encoding="utf-8") as f:
        f.write("\n$ " + " ".join(str(c) for c in cmd) + "\n")
        f.flush()
        code = subprocess.call(cmd, cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT,
                               env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if code != 0:
        raise SystemExit(f"실패 (exit {code}) — 로그: {log}")


def evaluate(adapter: Path, report_dir: Path, log: Path, with_val: bool) -> dict[str, Score]:
    scores: dict[str, Score] = {}
    targets = [(name, ["--eval-file", str(path)]) for name, path in EVAL_SETS.items()]
    if with_val:
        targets.append(("db_val", ["--eval-source", "db-val"]))
    for name, extra in targets:
        report = report_dir / f"eval_{name}.json"
        run([sys.executable, str(LORA / "eval_parser.py"), "--parsers", "lora", "--adapter", str(adapter),
             "--report", str(report), *extra], log)
        data = json.loads(report.read_text(encoding="utf-8"))
        n = int(data["n"])
        scores[name] = Score(round(data["results"]["lora"]["accuracy"]["exact"] * n), n)
    return scores


def main() -> int:
    ap = argparse.ArgumentParser(description="승인 사용자 데이터 LoRA 재학습 루프")
    ap.add_argument("--min-new", type=int, default=int(os.environ.get("LORA_RETRAIN_MIN_NEW", 200)),
                    help="새 승인 문장이 이 수 이상일 때만 재학습 (기본 200)")
    ap.add_argument("--force", action="store_true", help="기준 무시")
    ap.add_argument("--no-augment", action="store_true", help="증강 생략")
    ap.add_argument("--per-sample", type=int, default=6, help="증강: 문장당 생성 수")
    ap.add_argument("--max-drop", type=int, default=1, help="어느 평가셋이든 이보다 더 떨어지면 불채택")
    ap.add_argument("--deploy", action="store_true", help="후보가 이기면 backend/models/lora 교체")
    args = ap.parse_args()

    sys.path.insert(0, str(LORA))
    sys.path.insert(0, str(ROOT / "backend"))
    from dataset import discover_db_samples

    state = load_state()
    samples = discover_db_samples(split="train")
    fresh = new_approved(samples, set(state.get("trained_ids", [])))
    val_n = len(discover_db_samples(split="val"))
    print(f"승인 문장 train {len(samples)}건 · val {val_n}건 · 지난 재학습 이후 새 승인 {len(fresh)}건 (기준 {args.min_new})")
    if len(fresh) < args.min_new and not args.force:
        print(f"재학습 대기 — {args.min_new - len(fresh)}건 더 승인되면 진행")
        return 0

    name = "user_" + datetime.now().strftime("%y%m%d_%H%M")
    run_dir = OUT / name
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / "retrain.log"
    if not args.no_augment and samples:
        run([sys.executable, str(LORA / "augment_prompts.py"), "--per-sample", str(args.per_sample),
             "--output", str(run_dir / "augment.jsonl")], log)
    aug = run_dir / "augment.jsonl"
    train_args = ["--name", name, "--augment-file", str(aug if aug.is_file() else run_dir / "none.jsonl")]
    run([sys.executable, str(ROOT / "scripts" / "fine_tune_lora.py"), *train_args], log)
    candidate_dir = run_dir / "adapter"

    cand = evaluate(candidate_dir, run_dir, log, with_val=val_n > 0)
    deployed = evaluate(DEPLOYED, run_dir / "deployed", log, with_val=val_n > 0) if DEPLOYED.is_dir() else {}
    (run_dir / "deployed").mkdir(exist_ok=True)
    win, why = decide(cand, deployed, args.max_drop) if deployed else (True, "배포본 없음")

    lines = [f"# LoRA 재학습 {name}", "",
             f"- 승인 train {len(samples)}건 (새 {len(fresh)}건) · val {val_n}건 · 증강 "
             f"{sum(1 for _ in aug.open(encoding='utf-8')) if aug.is_file() else 0}건",
             "", "| 평가셋 | 배포본 | 후보 |", "|--------|--------|------|"]
    for n in sorted(set(cand) | set(deployed)):
        d, c = deployed.get(n), cand.get(n)
        fmt = lambda s: f"{s.rate:.1%} ({s.correct}/{s.total})" if s else "-"  # noqa: E731
        lines.append(f"| {n} | {fmt(d)} | {fmt(c)} |")
    lines += ["", f"판정: **{'채택' if win else '불채택'}** — {why}"]

    deployed_now = False
    if win and args.deploy:
        if DEPLOYED.is_dir():
            backup = DEPLOYED.parent / f"lora_prev_{datetime.now():%y%m%d_%H%M}"
            shutil.move(str(DEPLOYED), str(backup))
            lines.append(f"- 이전 배포본 → `{backup.relative_to(ROOT)}`")
        shutil.copytree(candidate_dir, DEPLOYED)
        deployed_now = True
        lines.append("- 배포본 교체 완료 — 백엔드 재시작 필요 (LLM_PROVIDER=lora 일 때 사용)")
    elif win:
        lines.append("- `--deploy` 로 다시 실행하면 교체")

    report = run_dir / "retrain_report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n보고서 → {report}")

    state.setdefault("runs", []).append({"name": name, "win": win, "deployed": deployed_now, "why": why,
                                         "candidate": {k: vars(v) for k, v in cand.items()},
                                         "deployed_scores": {k: vars(v) for k, v in deployed.items()}})
    state["trained_ids"] = sorted({s.payload.get("sample_id") for s in samples if s.payload.get("sample_id")})
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
