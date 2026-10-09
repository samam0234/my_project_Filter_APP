#!/usr/bin/env python3
"""영상 · GIF 대상 지우기 비교 — 프레임마다 Telea vs 배경판(다른 프레임에서 보인 배경 + 안 보인 곳만 LaMa 한 번).

정답이 있는 합성 영상을 만든다: COCO 사진 한 장을 배경으로 고정하고, 다른 사진의 사람 모양을 잘라 붙여 프레임마다 옮긴다.
지운 결과를 원래 배경(정답)과 비교한다. 세그멘테이션은 빼고(붙인 자리 = 마스크) 메우기만 잰다.

시나리오
  moving : 사람이 화면을 가로질러 움직인다 (배경이 다른 프레임에서 보인다) — 일반적인 고정 카메라 영상
  still  : 사람이 제자리에 서 있다 (배경이 한 번도 안 보인다 → 배경판도 결국 LaMa 한 번)
  pan    : 카메라가 옆으로 움직인다 (배경판을 쓰면 안 된다 — 고정 카메라 판정이 맞는지)
지표 (구멍 안): L1 · PSNR, 깜빡임(연속 프레임 사이 결과 차이 — 정답은 0), 처리 시간, 고정 카메라 판정

실행: python scripts/experiments/video_removal_eval.py --n 20 --out docs/vaildates/video_removal_eval_20261009.json
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

from app.services import video_inpaint  # noqa: E402
from app.services.effects import apply_remove_object  # noqa: E402

FRAMES = 16
SIDE = 480


def make_clip(bg: np.ndarray, donor_img: np.ndarray, donor_mask: np.ndarray, frac: float, mode: str, rng):
    """(frames, masks, truth) — truth 는 프레임마다의 정답 배경."""
    h, w = bg.shape[:2]
    ys, xs = np.nonzero(donor_mask)
    crop_m = donor_mask[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1].astype(np.uint8)
    crop_i = donor_img[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]
    scale = np.sqrt(frac * h * w / max(1, crop_m.sum()))
    sh, sw = int(crop_m.shape[0] * scale), int(crop_m.shape[1] * scale)
    sh, sw = min(sh, h - 2), min(sw, int(w * 0.45))
    crop_m = cv2.resize(crop_m, (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    crop_i = cv2.resize(crop_i, (sw, sh), interpolation=cv2.INTER_AREA)
    y = h - sh - 1
    frames, masks, truth = [], [], []
    pad = 40  # pan 용 여유
    wide = cv2.copyMakeBorder(bg, 0, 0, pad, pad, cv2.BORDER_REFLECT) if mode == "pan" else None
    for t in range(FRAMES):
        if mode == "moving":
            x = int((w - sw) * t / (FRAMES - 1))
            base = bg
        elif mode == "still":
            x = (w - sw) // 2
            base = bg
        else:  # pan: 카메라가 움직여 배경이 프레임마다 밀린다, 사람은 화면 가운데
            off = int(2 * pad * t / (FRAMES - 1))
            base = wide[:, off: off + w]
            x = (w - sw) // 2
        frame = base.copy()
        region = frame[y: y + sh, x: x + sw]
        region[crop_m] = crop_i[crop_m]
        mask = np.zeros((h, w), np.uint8)
        mask[y: y + sh, x: x + sw][crop_m] = 255
        frames.append(frame)
        masks.append(mask)
        truth.append(base)
    return frames, masks, truth


def score(outs, masks, truth):
    l1, psnr, flick = [], [], []
    holes = [video_inpaint._dilate(m) for m in masks]  # 평가 구멍 = 두 방법이 실제로 메우는 자리
    for o, hole, gt in zip(outs, holes, truth):
        d = (o[hole].astype(np.float32) - gt[hole].astype(np.float32))
        l1.append(float(np.abs(d).mean()))
        mse = float((d ** 2).mean())
        psnr.append(99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse))
    for i in range(1, len(outs)):
        both = holes[i] | holes[i - 1]
        # 정답 배경이 같은 곳(고정 카메라)만 깜빡임으로 본다
        same = (np.abs(truth[i].astype(np.int16) - truth[i - 1].astype(np.int16)).max(axis=2) == 0) & both
        if same.any():
            flick.append(float(np.abs(outs[i].astype(np.float32) - outs[i - 1].astype(np.float32))[same].mean()))
    return {"l1": float(np.mean(l1)), "psnr": float(np.mean(psnr)), "flicker": float(np.mean(flick)) if flick else 0.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--samples", type=Path)
    args = ap.parse_args()
    import leak_eval as L

    pool = L.load_gt()
    rng = np.random.default_rng(1)
    persons = [(gt, i) for gt in pool for i in gt.instances if i["cat"] == "person" and i["area"] > 0.04 * gt.shape[0] * gt.shape[1]]
    rows = []
    for k, gt in enumerate(pool):
        if len(rows) >= args.n * 3:
            break
        bg = cv2.imread(str(gt.path))
        if bg is None or any(i["cat"] == "person" for i in gt.instances):
            continue  # 배경에 사람이 없는 사진만 (정답 배경을 깨끗하게)
        s = SIDE / max(bg.shape[:2])
        bg = cv2.resize(bg, (int(bg.shape[1] * s), int(bg.shape[0] * s)), interpolation=cv2.INTER_AREA)
        dgt, inst = persons[int(rng.integers(len(persons)))]
        dimg = cv2.imread(str(dgt.path))
        frac = float(rng.choice([0.08, 0.18]))
        for mode in ("moving", "still", "pan"):
            frames, masks, truth = make_clip(bg, dimg, inst["mask"], frac, mode, rng)
            t0 = time.perf_counter()
            old = [apply_remove_object(f, m, engine="telea") for f, m in zip(frames, masks)]
            t_old = time.perf_counter() - t0
            it = iter(masks)
            t0 = time.perf_counter()
            plan = video_inpaint.build_plan(frames, lambda f: next(it))
            new = [video_inpaint.render(f, i, plan) for i, f in enumerate(frames)]
            t_new = time.perf_counter() - t0
            row = {"image": gt.path.name, "mode": mode, "frac": frac, "static": plan.static, "seen_ratio": plan.seen_ratio,
                   "old_s": t_old, "new_s": t_new}
            row.update({f"old_{a}": b for a, b in score(old, masks, truth).items()})
            row.update({f"new_{a}": b for a, b in score(new, masks, truth).items()})
            rows.append(row)
            if args.samples and mode == "moving" and len(rows) <= 9:
                args.samples.mkdir(parents=True, exist_ok=True)
                mid = FRAMES // 2
                strip = np.hstack([frames[mid], old[mid], new[mid]])
                cv2.imwrite(str(args.samples / f"{len(rows):02d}_{gt.path.stem}.jpg"), strip, [cv2.IMWRITE_JPEG_QUALITY, 85])

    rng2 = np.random.default_rng(0)
    report = {}
    for mode in ("moving", "still", "pan"):
        sel = [r for r in rows if r["mode"] == mode]
        if not sel:
            continue
        out = {"n": len(sel), "static_detected": float(np.mean([r["static"] for r in sel])), "seen_ratio": float(np.mean([r["seen_ratio"] for r in sel]))}
        for m in ("l1", "psnr", "flicker"):
            d = np.array([r[f"new_{m}"] - r[f"old_{m}"] for r in sel])
            boots = [rng2.choice(d, len(d)).mean() for _ in range(2000)]
            out[m] = {"old": float(np.mean([r[f"old_{m}"] for r in sel])), "new": float(np.mean([r[f"new_{m}"] for r in sel])),
                      "diff_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
        out["time_s"] = {"old": float(np.mean([r["old_s"] for r in sel])), "new": float(np.mean([r["new_s"] for r in sel]))}
        report[mode] = out
        print(f"{mode:7} n={out['n']:2} 고정판정 {out['static_detected']*100:.0f}% 보인비율 {out['seen_ratio']*100:.0f}% | "
              f"L1 {out['l1']['old']:.1f}→{out['l1']['new']:.1f} {np.round(out['l1']['diff_ci95'],1)} | "
              f"PSNR {out['psnr']['old']:.1f}→{out['psnr']['new']:.1f} | 깜빡임 {out['flicker']['old']:.1f}→{out['flicker']['new']:.1f} | "
              f"{out['time_s']['old']:.2f}→{out['time_s']['new']:.2f}s/{FRAMES}프레임")
    if args.out:
        args.out.write_text(json.dumps({"frames": FRAMES, "side": SIDE, "summary": report, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
