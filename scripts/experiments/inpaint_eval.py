#!/usr/bin/env python3
"""대상 지우기 빈자리 메우기 비교 — Telea vs LaMa (정답이 있는 구멍으로).

실제 물체를 지우면 "원래 그 뒤에 뭐가 있었는지" 정답이 없다. 그래서 COCO 사진의 **배경 위에** 다른 사진의 사람 모양 구멍을
얹고(그 자리 원래 픽셀이 정답), 두 방법으로 메운 뒤 구멍 안 오차를 잰다.

지표 (구멍 안에서만):
  - L1 (0~255, 낮을수록 좋음)
  - PSNR (dB, 높을수록 좋음)
  - 경사 오차: 소벨 경사 크기 차이 (낮을수록 좋음) — Telea 는 매끈하게 번져 무늬(경사)를 잃는다
  - 처리 시간 (ms)
구멍 크기(사진 면적 대비)별로 나눠 본다 — "큰 물체일수록 번진다"를 확인하려고.

실행: python scripts/experiments/inpaint_eval.py --n 60 --out docs/vaildates/inpaint_eval_20261009.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

from app.core.config import get_settings  # noqa: E402
from app.services.effects import apply_remove_object  # noqa: E402

BUCKETS = [(0.0, 0.05, "작음 <5%"), (0.05, 0.15, "중간 5~15%"), (0.15, 1.0, "큼 ≥15%")]


def grad(img: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))


def metrics(orig: np.ndarray, filled: np.ndarray, hole: np.ndarray) -> dict:
    o, f = orig[hole].astype(np.float32), filled[hole].astype(np.float32)
    l1 = float(np.abs(o - f).mean())
    mse = float(((o - f) ** 2).mean())
    psnr = 99.0 if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))
    gerr = float(np.abs(grad(orig)[hole] - grad(filled)[hole]).mean())
    return {"l1": l1, "psnr": psnr, "grad_err": gerr}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--samples", type=Path, help="비교 이미지 몇 장을 저장할 폴더")
    args = ap.parse_args()

    import leak_eval as L

    pool = L.load_gt()
    rng = np.random.default_rng(0)
    persons = [i for gt in pool for i in gt.instances if i["cat"] == "person"]
    rows = []
    for gt in pool:
        if len(rows) >= args.n:
            break
        img = cv2.imread(str(gt.path))
        if img is None:
            continue
        h, w = img.shape[:2]
        occupied = np.zeros((h, w), bool)
        for inst in gt.instances:
            occupied |= inst["mask"]
        # 다른 사진의 사람 모양을 이 사진 배경 위에 얹는다 (물체와 겹치지 않는 자리)
        donor = persons[int(rng.integers(len(persons)))]["mask"].astype(np.uint8)
        ys, xs = np.nonzero(donor)
        if len(xs) == 0:
            continue
        shape = donor[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]
        target_frac = float(rng.choice([0.03, 0.08, 0.2]))
        scale = np.sqrt(target_frac * h * w / max(1, shape.sum()))
        sh, sw = max(4, int(shape.shape[0] * scale)), max(4, int(shape.shape[1] * scale))
        if sh >= h or sw >= w:
            continue
        shape = cv2.resize(shape, (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
        placed = None
        for _ in range(30):
            y, x = int(rng.integers(0, h - sh)), int(rng.integers(0, w - sw))
            if not (occupied[y: y + sh, x: x + sw] & shape).any():
                placed = (y, x)
                break
        if placed is None:
            continue
        hole = np.zeros((h, w), bool)
        hole[placed[0]: placed[0] + sh, placed[1]: placed[1] + sw] = shape
        mask = hole.astype(np.uint8) * 255
        row = {"image": gt.path.name, "hole_frac": float(hole.mean())}
        outs = {}
        for engine in ("telea", "lama"):
            t0 = time.perf_counter()
            filled = apply_remove_object(img, mask, engine=engine)
            row[f"{engine}_ms"] = (time.perf_counter() - t0) * 1000
            # 평가 구멍 = 실제로 메운 영역(팽창 포함)과 같게 — 원 구멍 안에서만 잰다
            row.update({f"{engine}_{k}": v for k, v in metrics(img, filled, hole).items()})
            outs[engine] = filled
        rows.append(row)
        if args.samples and len(rows) <= 8:
            args.samples.mkdir(parents=True, exist_ok=True)
            holed = img.copy()
            holed[hole] = (255, 0, 255)
            strip = np.hstack([cv2.resize(x, (320, int(320 * h / w))) for x in (holed, outs["telea"], outs["lama"])])
            cv2.imwrite(str(args.samples / f"{len(rows):02d}_{gt.path.stem}.jpg"), strip, [cv2.IMWRITE_JPEG_QUALITY, 85])

    def summary(sel):
        if not sel:
            return None
        out = {"n": len(sel)}
        for engine in ("telea", "lama"):
            for k in ("l1", "psnr", "grad_err", "ms"):
                out[f"{engine}_{k}"] = float(np.mean([r[f"{engine}_{k}"] for r in sel]))
        out["lama_better_l1"] = float(np.mean([r["lama_l1"] < r["telea_l1"] for r in sel]))
        out["lama_better_grad"] = float(np.mean([r["lama_grad_err"] < r["telea_grad_err"] for r in sel]))
        return out

    report = {"all": summary(rows)}
    for lo, hi, name in BUCKETS:
        report[name] = summary([r for r in rows if lo <= r["hole_frac"] < hi])
    for name, s in report.items():
        if s:
            print(f"{name:10} n={s['n']:3} | L1 telea {s['telea_l1']:.1f} → lama {s['lama_l1']:.1f} | PSNR {s['telea_psnr']:.1f} → {s['lama_psnr']:.1f} dB"
                  f" | 경사오차 {s['telea_grad_err']:.1f} → {s['lama_grad_err']:.1f} | LaMa 가 나은 비율 L1 {s['lama_better_l1']*100:.0f}% 경사 {s['lama_better_grad']*100:.0f}%"
                  f" | {s['telea_ms']:.0f} → {s['lama_ms']:.0f} ms")
    if args.out:
        args.out.write_text(json.dumps({"summary": report, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    get_settings()
    main()
