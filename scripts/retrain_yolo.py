#!/usr/bin/env python3
"""세그 모델(YOLO26-seg) 재학습 루프 — 어려운 사례 수집 → 라벨 → 이어 학습 → 평가 → 판정 → (선택) 배포.

남은 품질 약점은 "사람이 맞닿거나 겹친 사진"에서 고른 사람에 옆 사람 조각이 섞이거나(섞임 5% 초과),
다른 사람을 고르는 것(오선택)이다 (docs/vaildates/leak-diagnosis-20261008.md). 후처리로 줄일 만큼 줄였으므로
모델 자체를 그런 사진에 더 익숙하게 만드는 길을 준비한다.

단계
  collect  COCO train2017 주석에서 **어려운 사례**(화면 2.5% 이상인 인스턴스 둘 이상이 맞닿거나 겹친 사진)와
           **일반 사진**(잊지 않게 섞는 몫)을 고르고, 이미지를 받아(캐시) YOLO-seg 라벨(80클래스, 모델 names 순서)로 쓴다.
           `--extra` 로 직접 라벨링한 YOLO-seg 폴더(서비스에서 실패한 사진 등)를 더 넣을 수 있다.
  train    배포 모델에서 이어 학습 (낮은 학습률, 몇 에폭)
  eval     후보와 배포 모델을 같은 조건으로 —
             (1) 섞임 평가(scripts/experiments/leak_eval.py 시나리오, COCO val2017 정답): 선택 정확 · 섞임 5% 초과 비율 · IoU
             (2) 일반 성능: COCO val2017 의 다른 사진(섞임 평가에 안 쓴 것)으로 마스크 mAP50-95
  decide   일반 성능이 MAX_MAP_DROP 넘게 떨어지지 않고, 어려운 시나리오의 섞임 · 선택이 나빠지지 않으면서 하나라도 좋아져야 채택
  deploy   `--deploy` 이고 채택이면 backend/models/<모델> 을 백업하고 교체

데이터 · 결과는 git 밖: training/datasets/yolo_hard/ · training/outputs/segment/<run>/
실행: python scripts/retrain_yolo.py --hard 1500 --replay 1500 --epochs 8
      python scripts/retrain_yolo.py --skip-collect --skip-train --candidate <best.pt>   # 평가만
"""

from __future__ import annotations

import argparse
import contextlib
import json
import random
import shutil
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

ANN_TRAIN = ROOT / "training/datasets/coco_raw/annotations/instances_train2017.json"
ANN_VAL = ROOT / "training/datasets/coco_raw/annotations/instances_val2017.json"
DATA = ROOT / "training/datasets/yolo_hard"
OUT = ROOT / "training/outputs/segment"
MODELS = ROOT / "backend/models"
BIG = 0.025
SCENARIOS = ("left", "rank2", "touching", "all_persons", "dog")
HARD_SCENARIOS = ("touching", "rank2")
MAX_MAP_DROP = 0.005  # 마스크 mAP50-95 하락 허용 (0.5%p)


# --------------------------------------------------------------------------- collect


def _polys(ann) -> list[np.ndarray]:
    return [np.array(p, np.float32).reshape(-1, 2) for p in ann["segmentation"] if len(p) >= 6]


def _is_hard(anns, w, h) -> bool:
    """큰 인스턴스 둘 이상이 맞닿거나 겹친다 (박스를 조금 넓혀 겹치면 맞닿은 것으로 본다)."""
    bigs = [a for a in anns if a["area"] >= BIG * w * h]
    pad = 0.02 * max(w, h)
    for i in range(len(bigs)):
        x0, y0, bw, bh = bigs[i]["bbox"]
        for j in range(i + 1, len(bigs)):
            x1, y1, cw, ch = bigs[j]["bbox"]
            if x0 - pad < x1 + cw and x1 - pad < x0 + bw and y0 - pad < y1 + ch and y1 - pad < y0 + bh:
                return True
    return False


def _download(url: str, dst: Path) -> bool:
    if dst.is_file() and dst.stat().st_size > 0:
        return True
    tmp = dst.with_suffix(".part")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dst)
        return True
    except Exception:  # noqa: BLE001 — 받다 실패한 사진은 건너뛴다
        tmp.unlink(missing_ok=True)
        return False


def _write_split(name: str, items, info, by_image, cat_to_idx, workers: int) -> int:
    img_dir = DATA / "images" / name
    lbl_dir = DATA / "labels" / name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(info[i]["coco_url"], img_dir / info[i]["file_name"]) for i in items]
    with ThreadPoolExecutor(workers) as ex:
        ok = list(ex.map(lambda a: _download(*a), jobs))
    n = 0
    for iid, good in zip(items, ok):
        if not good:
            continue
        im = info[iid]
        w, h = im["width"], im["height"]
        lines = []
        for a in by_image[iid]:
            k = cat_to_idx.get(a["category_id"])
            if k is None:
                continue
            for poly in _polys(a):
                xy = (poly / [w, h]).clip(0, 1).reshape(-1)
                lines.append(f"{k} " + " ".join(f"{v:.5f}" for v in xy))
        (lbl_dir / (Path(im["file_name"]).stem + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
        n += 1
    return n


def collect(args, names: dict[int, str]) -> Path:
    """COCO 주석 → 어려운 사례 + 일반 사진 → YOLO-seg 데이터셋 yaml."""
    import leak_eval as L

    rng = random.Random(args.seed)
    print("COCO train2017 주석 읽는 중 (약 450MB)…", flush=True)
    data = json.loads(ANN_TRAIN.read_text(encoding="utf-8"))
    name_to_idx = {v: k for k, v in names.items()}
    cat_to_idx = {c["id"]: name_to_idx[c["name"]] for c in data["categories"] if c["name"] in name_to_idx}
    info = {i["id"]: i for i in data["images"]}
    by_image: dict[int, list] = {}
    for a in data["annotations"]:
        if a.get("iscrowd") or not isinstance(a["segmentation"], list):
            continue
        by_image.setdefault(a["image_id"], []).append(a)
    hard = [i for i, anns in by_image.items() if _is_hard(anns, info[i]["width"], info[i]["height"])]
    rest = [i for i in by_image if i not in set(hard)]
    rng.shuffle(hard)
    rng.shuffle(rest)
    train_ids = hard[: args.hard] + rest[: args.replay]
    print(f"어려운 사례 후보 {len(hard)}장 중 {min(len(hard), args.hard)} + 일반 {min(len(rest), args.replay)}장", flush=True)
    n_train = _write_split("train", train_ids, info, by_image, cat_to_idx, args.workers)

    # 검증(학습 중 조기 판단용): val2017 중 섞임 평가에 쓰는 사진은 뺀다
    vdata = json.loads(ANN_VAL.read_text(encoding="utf-8"))
    vinfo = {i["id"]: i for i in vdata["images"]}
    vby: dict[int, list] = {}
    for a in vdata["annotations"]:
        if not a.get("iscrowd") and isinstance(a["segmentation"], list):
            vby.setdefault(a["image_id"], []).append(a)
    used = {int(p.stem) for d in L.IMAGE_DIRS for p in d.glob("*.jpg")}
    vids = sorted(i for i in vby if i not in used)
    rng.shuffle(vids)
    vcat = {c["id"]: name_to_idx[c["name"]] for c in vdata["categories"] if c["name"] in name_to_idx}
    n_val = _write_split("val", vids[: args.val], vinfo, vby, vcat, args.workers)

    yaml = DATA / "data.yaml"
    lines = [f"path: {DATA.as_posix()}", "train: images/train", "val: images/val", "names:"]
    lines += [f"  {k}: {v}" for k, v in sorted(names.items())]
    yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for extra in args.extra or []:
        print(f"추가 데이터: {extra} (images/ labels/ 를 train 에 합침)")
        for sub in ("images", "labels"):
            for f in (extra / sub).glob("*"):
                shutil.copy2(f, DATA / sub / "train" / f.name)
    print(f"데이터셋: 학습 {n_train}장 · 검증 {n_val}장 → {yaml}", flush=True)
    (DATA / "collect.json").write_text(json.dumps({"hard": min(len(hard), args.hard), "replay": min(len(rest), args.replay),
                                                   "train": n_train, "val": n_val, "seed": args.seed}, indent=2), encoding="utf-8")
    return yaml


# --------------------------------------------------------------------------- eval


_PROCS: dict = {}  # 모델 경로 → ImageProcessor (사진마다 모델을 다시 읽지 않게)


@contextlib.contextmanager
def _serving_with(model_path: Path):
    """서빙 경로(nodes._processor)를 이 모델로 바꿔 끼운다 — 후처리 설정은 지금 서비스 그대로."""
    import leak_eval as L
    from app.core.config import get_settings
    from app.services.image_processor import ImageProcessor
    from app.services.segmentation import Segmentor
    from app.workflows import nodes

    key = str(model_path)
    if key not in _PROCS:
        cfg = get_settings().model_copy(update={"yolo_model_path": key, "seg_prefer_onnx": False})
        _PROCS[key] = ImageProcessor(cfg, segmentor=Segmentor(cfg))
    with L._patch(nodes, _processor=_PROCS[key]):
        yield


def leak_scores(model_path: Path, n: int) -> dict:
    import leak_eval as L

    pool = L.load_gt()
    tmp = Path(tempfile.mkdtemp(prefix="yolo-eval-"))
    out = {}
    try:
        for scen in SCENARIOS:
            cases = L.scenario_cases(scen, pool)[:n]
            rows = [L.run_case(c, tmp, lambda: _serving_with(model_path)) for c in cases]
            s = L.summarize(rows)
            f = s.get("final", {})
            out[scen] = {"n": s["n"], "pick_ok": s["pick_ok"], "leak": f.get("leak"), "leak_case5": f.get("leak_case5"),
                         "iou": f.get("iou"), "cover": f.get("cover")}
            print(f"  {scen:12} n={s['n']:3} 선택 {s['pick_ok']} 섞임 {f.get('leak')} (5%초과 {f.get('leak_case5')}) IoU {f.get('iou')}", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def map_score(model_path: Path, yaml: Path, device) -> float | None:
    if not yaml.is_file():
        return None
    from ultralytics import YOLO

    res = YOLO(str(model_path)).val(data=str(yaml), split="val", imgsz=640, batch=8, device=device, plots=False, verbose=False)
    return float(res.seg.map)


def decide(cand: dict, base: dict, cand_map, base_map) -> tuple[bool, str]:
    why = []
    if cand_map is not None and base_map is not None and cand_map < base_map - MAX_MAP_DROP:
        return False, f"일반 성능 하락: mask mAP {base_map:.4f} → {cand_map:.4f}"
    better = False
    for scen in SCENARIOS:
        c, b = cand[scen], base[scen]
        if c["pick_ok"] is not None and b["pick_ok"] is not None and c["pick_ok"] < b["pick_ok"] - 0.02:
            return False, f"{scen} 선택 정확 하락 {b['pick_ok']} → {c['pick_ok']}"
        if c["leak_case5"] is not None and b["leak_case5"] is not None and c["leak_case5"] > b["leak_case5"] + 0.02:
            return False, f"{scen} 섞임 5% 초과 비율 상승 {b['leak_case5']} → {c['leak_case5']}"
        if scen in HARD_SCENARIOS and c["leak_case5"] is not None and b["leak_case5"] is not None and c["leak_case5"] < b["leak_case5"] - 0.02:
            better = True
            why.append(f"{scen} 섞임 5% 초과 {b['leak_case5']} → {c['leak_case5']}")
        if scen in HARD_SCENARIOS and (c["pick_ok"] or 0) > (b["pick_ok"] or 0) + 0.02:
            better = True
            why.append(f"{scen} 선택 {b['pick_ok']} → {c['pick_ok']}")
    if not better:
        return False, "어려운 시나리오에서 2%p 넘게 좋아진 지표 없음"
    return True, "; ".join(why)


# --------------------------------------------------------------------------- main


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.4f}"


def main() -> int:
    ap = argparse.ArgumentParser(description="YOLO 세그 재학습 루프")
    ap.add_argument("--model", default="yolo26m-seg.pt", help="backend/models 안의 배포 모델 (이어 학습 시작점 · 비교 기준)")
    ap.add_argument("--hard", type=int, default=1500)
    ap.add_argument("--replay", type=int, default=1500)
    ap.add_argument("--val", type=int, default=500)
    ap.add_argument("--extra", type=Path, nargs="*", help="직접 라벨링한 YOLO-seg 폴더 (images/ labels/)")
    # 기본은 보수적 미세 조정 — 첫 시도(lr0 5e-4 · 앞 10층 고정 · 워밍업 편향 학습률 0.1)는 1 에폭 만에 mAP 0.428 → 0.334 로 무너졌다
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr0", type=float, default=0.0001)
    ap.add_argument("--freeze", type=int, default=23, help="앞쪽 층 고정 수 (YOLO26m 은 24층 — 23 이면 Segment 머리만 학습)")
    ap.add_argument("--warmup-epochs", type=float, default=0.0, help="워밍업 (켜면 편향 학습률도 lr0 로 — ultralytics 기본 0.1 은 미세 조정에 너무 크다)")
    ap.add_argument("--mosaic", type=float, default=0.5, help="모자이크 증강 확률")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--device", default=0)
    ap.add_argument("--workers", type=int, default=16, help="이미지 받기 동시 수")
    ap.add_argument("--train-workers", type=int, default=2,
                    help="학습 데이터 로더 프로세스 수 (Windows 는 프로세스마다 메모리를 크게 써 8개면 16GB 에서 모자랐다)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-eval", type=int, default=150,
                    help="섞임 평가 시나리오마다 사진 수 상한 (있는 만큼 — leak_eval.py --download-touching 으로 늘린다. 48장이면 1장이 2%%p)")
    ap.add_argument("--skip-collect", action="store_true")
    ap.add_argument("--collect-only", action="store_true", help="데이터만 만들고 끝 (GPU 를 다른 일이 쓰는 동안)")
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--candidate", type=Path, help="--skip-train 일 때 평가할 후보 .pt")
    ap.add_argument("--deploy", action="store_true", help="채택이면 backend/models/<모델> 교체 (백업 남김)")
    args = ap.parse_args()

    from ultralytics import YOLO

    base_path = MODELS / args.model
    names = YOLO(str(base_path)).names
    yaml = DATA / "data.yaml"
    if not args.skip_collect:
        yaml = collect(args, names)
    if args.collect_only:
        return 0

    run = "hard_" + datetime.now().strftime("%y%m%d_%H%M")
    run_dir = OUT / run
    if args.skip_train:
        if not args.candidate:
            raise SystemExit("--skip-train 이면 --candidate 를 주세요")
        cand_path = args.candidate
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        t0 = time.time()
        YOLO(str(base_path)).train(
            data=str(yaml), epochs=args.epochs, imgsz=640, batch=args.batch, lr0=args.lr0, lrf=0.1, warmup_epochs=args.warmup_epochs, warmup_bias_lr=args.lr0, mosaic=args.mosaic,
            freeze=args.freeze, device=args.device, project=str(OUT), name=run, exist_ok=True, plots=False,
            optimizer="AdamW", close_mosaic=max(1, args.epochs // 2), seed=args.seed, workers=args.train_workers,
        )
        cand_path = run_dir / "weights" / "best.pt"
        print(f"학습 {time.time() - t0:.0f}초 → {cand_path}", flush=True)

    print("평가: 배포 모델", flush=True)
    base = leak_scores(base_path, args.n_eval)
    base_map = map_score(base_path, yaml, args.device)
    print("평가: 후보", flush=True)
    cand = leak_scores(cand_path, args.n_eval)
    cand_map = map_score(cand_path, yaml, args.device)
    win, why = decide(cand, base, cand_map, base_map)

    lines = [f"# YOLO 재학습 {run}", "", f"- 시작 모델 `{args.model}` · 후보 `{cand_path}`",
             f"- mask mAP50-95 (val {args.val}장): 배포 {_fmt(base_map)} → 후보 {_fmt(cand_map)}",
             f"- 설정: epochs {args.epochs} · lr0 {args.lr0} · freeze {args.freeze} · warmup {args.warmup_epochs} · mosaic {args.mosaic}", "",
             "| 시나리오 | 선택 정확 (배포 → 후보) | 섞임 5% 초과 | 평균 섞임 | IoU |", "|---|---|---|---|---|"]
    for s in SCENARIOS:
        b, c = base[s], cand[s]
        lines.append(f"| {s} (n={c['n']}) | {b['pick_ok']} → {c['pick_ok']} | {b['leak_case5']} → {c['leak_case5']} | "
                     f"{b['leak']} → {c['leak']} | {b['iou']} → {c['iou']} |")
    lines += ["", f"판정: **{'채택' if win else '불채택'}** — {why}"]
    if win and args.deploy:
        backup = MODELS / f"{Path(args.model).stem}_prev_{datetime.now():%y%m%d_%H%M}.pt"
        shutil.copy2(base_path, backup)
        shutil.copy2(cand_path, base_path)
        lines.append(f"- 배포: `{base_path.relative_to(ROOT)}` 교체, 이전 → `{backup.relative_to(ROOT)}` — 백엔드 재시작 필요"
                     " (ONNX 로 서빙하면 scripts/convert_to_onnx.py 로 다시 내보내기)")
    elif win:
        lines.append("- `--deploy` 로 다시 실행하면 교체")
    report = run_dir / "retrain_report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "retrain_scores.json").write_text(json.dumps(
        {"run": run, "model": args.model, "win": win, "why": why, "base": base, "candidate": cand,
         "base_map": base_map, "candidate_map": cand_map, "args": {k: str(v) for k, v in vars(args).items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n보고서 → {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
