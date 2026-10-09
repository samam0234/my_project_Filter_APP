#!/usr/bin/env python3
"""실제 영상(DAVIS 2017)으로 영상 기능 검증 — 합성 영상 평가의 한계(일정한 걸음 · 평면 배경)를 넘어서.

DAVIS 2017 trainval 480p: 실제 촬영 영상 90개, 사람이 그린 인스턴스 정답 마스크 (CC BY 4.0 — Pont-Tuset et al. 2017).
받기: training/datasets/davis/ 에 DAVIS-2017-trainval-480p.zip 을 풀어 둔다 (git 밖).

  tracking : 첫 프레임에서 사람이 둘 이상인 영상 — 실제 YOLO 세그로 "가장 왼쪽 사람"을 고르고, 첫 프레임에 고른 그 사람을
             끝까지 따라가는지 (대상 = 첫 프레임 결과와 IoU 0.5 이상인 정답 객체, 없으면 그 영상은 뺀다 — DAVIS 는 주요 인물만 그린다).
             정답 객체 중 사람은 첫 프레임에서 YOLO 사람 검출과 IoU 0.5 이상인 것. 대상이 15% 미만으로 보이는 프레임은 채점 제외.
             맞음 = 대상 IoU ≥ 0.1 이고 다른 정답 객체보다 대상과 더 겹침.
             추적(VIDEO_TRACK_INSTANCES) vs 프레임마다 다시 고름 — 맞은 프레임 비율 · 후반 1/3 · 대상 IoU
  removal  : 실제 영상(진짜 카메라 움직임 · 시차 · 조명)에 다른 사진의 사람을 잘라 붙여 가로질러 걷게 하고 지운다.
             원래 영상이 정답 → 구멍 안 L1 · 깜빡임. 예전(프레임마다 Telea) vs 지금(배경판: static / aligned / frame 자동)
             원래 영상의 움직이는 대상(DAVIS 정답 객체)이 있는 자리는 채점에서 뺀다 (배경판이 그 물체를 지운 것과 섞이지 않게)

실행: python scripts/experiments/davis_eval.py tracking --out docs/vaildates/davis_tracking_20261010.json
      python scripts/experiments/davis_eval.py removal --n 30 --out docs/vaildates/davis_removal_20261010.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

DAVIS = ROOT / "training" / "datasets" / "davis" / "DAVIS"
HIDDEN = 0.15


def sequences() -> list[str]:
    names = []
    for split in ("train", "val"):
        names += (DAVIS / "ImageSets" / "2017" / f"{split}.txt").read_text().split()
    return sorted(set(names))


def load(seq: str, limit: int | None = None):
    """(frames BGR 목록, 정답 라벨 맵 목록 — 0 배경, 1..N 객체)."""
    jp = sorted((DAVIS / "JPEGImages" / "480p" / seq).glob("*.jpg"))[:limit]
    frames = [cv2.imread(str(p)) for p in jp]
    labels = [np.array(Image.open(DAVIS / "Annotations" / "480p" / seq / (p.stem + ".png"))) for p in jp]
    return frames, labels


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 0.0


# --------------------------------------------------------------------------- tracking


def tracking(args) -> dict:
    from app.core.config import Settings
    from app.schemas.request import InstanceSelector, ParsedPrompt
    from app.services.segmentation import Segmentor
    from app.services.video_processor import FrameRenderer

    seg = Segmentor(Settings.model_validate({"DB_DIALECT": "sqlite", "PRELOAD_MODELS": False, "SEG_PREFER_ONNX": False}))
    rows = []
    for name in sequences():
        frames, labels = load(name, args.max_frames)
        first = labels[0]
        ids = [i for i in np.unique(first) if i != 0]
        if len(ids) < 2:
            continue
        det = seg.predict(frames[0], targets=["person"])
        persons = []
        for i in ids:
            m = first == i
            if m.sum() < 0.005 * m.size:
                continue
            if any(iou(m, inst.mask > 0) >= 0.5 for inst in det.instances):
                persons.append(i)
        if len(persons) < 2:
            continue
        full = {i: max((lab == i).sum() for lab in labels) for i in ids}
        row = {"seq": name, "frames": len(frames), "persons": len(persons)}
        target = None
        for track in (False, True):
            parsed = ParsedPrompt(target=["person"], effect="remove_bg", selector=InstanceSelector(position="left"))
            r = FrameRenderer(parsed, seg, smoothing="off", track=track)
            ok, ious, after = [], [], []
            for t, f in enumerate(frames):
                m = r.mask(f) > 127
                if t == 0 and target is None:
                    # 대상 = 시스템이 첫 프레임에서 실제로 고른 사람에 대응하는 정답 객체 (DAVIS 는 주요 인물만 그려
                    # "가장 왼쪽"이 정답 없는 군중일 수 있다 — 그런 영상은 뺀다)
                    best = max(ids, key=lambda i: iou(m, first == i))
                    if iou(m, first == best) < 0.5:
                        break
                    target = best
                tgt = labels[t] == target
                if tgt.sum() < HIDDEN * full[target]:
                    continue
                best_other = max(iou(m, labels[t] == o) for o in ids if o != target)
                good = iou(m, tgt) >= 0.1 and iou(m, tgt) > best_other  # 둘 다 0 이면 틀림
                ok.append(good)
                ious.append(iou(m, tgt))
                if t >= len(frames) * 2 // 3:
                    after.append(good)
            if target is None:
                break
            key = "track" if track else "frame"
            row[f"{key}_correct"] = float(np.mean(ok)) if ok else None
            row[f"{key}_after"] = float(np.mean(after)) if after else None
            row[f"{key}_iou"] = float(np.mean(ious)) if ious else None
            if track:
                t_ = r.tracker
                row.update({"reselected": t_.reselected, "reidentified": t_.reidentified, "reacquired": t_.reacquired} if t_ else {})
        if target is None:
            print(f"  {name:20} (건너뜀 — 첫 프레임에 고른 사람이 정답 객체가 아님)", flush=True)
            continue
        rows.append(row)
        print(f"  {name:20} 사람 {row['persons']} · {row['frames']}프레임 | 맞은 비율 {row['frame_correct']:.2f} → {row['track_correct']:.2f} | "
              f"후반 {row['frame_after']} → {row['track_after']} | IoU {row['frame_iou']:.2f} → {row['track_iou']:.2f}", flush=True)
    return {"rows": rows, "summary": _summary(rows, ("correct", "after", "iou"), ("frame", "track"))}


# --------------------------------------------------------------------------- removal


def _donor(rng, persons):
    gt, inst = persons[int(rng.integers(len(persons)))]
    img = cv2.imread(str(gt.path))
    m = inst["mask"]
    ys, xs = np.nonzero(m)
    return img[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1], m[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]


def removal(args) -> dict:
    import leak_eval as L
    from app.services import video_inpaint
    from app.services.effects import apply_remove_object

    pool = L.load_gt()
    persons = [(gt, i) for gt in pool for i in gt.instances if i["cat"] == "person" and i["area"] > 0.04 * gt.shape[0] * gt.shape[1]]
    rng = np.random.default_rng(5)
    rows = []
    for name in sequences():
        if len(rows) >= args.n:
            break
        frames, labels = load(name, args.max_frames)
        h, w = frames[0].shape[:2]
        di, dm = _donor(rng, persons)
        height = int(h * rng.uniform(0.45, 0.7))
        s = height / dm.shape[0]
        size = (max(4, int(dm.shape[1] * s)), height)
        di = cv2.resize(di, size, interpolation=cv2.INTER_AREA)
        dm = cv2.resize(dm.astype(np.uint8), size, interpolation=cv2.INTER_NEAREST) > 0
        y = h - height - 2
        n = len(frames)
        pasted, masks = [], []
        for t, f in enumerate(frames):
            x = int((w - size[0]) * t / max(1, n - 1))
            out = f.copy()
            region = out[y: y + height, x: x + size[0]]
            region[dm] = di[dm]
            m = np.zeros((h, w), np.uint8)
            m[y: y + height, x: x + size[0]][dm] = 255
            pasted.append(out)
            masks.append(m)
        t0 = time.perf_counter()
        old = [apply_remove_object(f, m, engine="telea") for f, m in zip(pasted, masks)]
        t_old = time.perf_counter() - t0
        it = iter(masks)
        t0 = time.perf_counter()
        plan = video_inpaint.build_plan(pasted, lambda f: next(it))
        new = [video_inpaint.render(f, i, plan) for i, f in enumerate(pasted)]
        t_new = time.perf_counter() - t0
        row = {"seq": name, "frames": n, "mode": plan.mode, "seen_ratio": plan.seen_ratio, "old_s": t_old, "new_s": t_new,
               "fallback_frames": plan.fallback_frames}
        for key, outs in (("old", old), ("new", new)):
            l1, flick = [], []
            for t in range(n):
                hole = video_inpaint._dilate(masks[t]) & (labels[t] == 0)  # 원래 영상의 움직이는 대상 자리는 뺀다
                if hole.sum() < 50:
                    continue
                l1.append(float(np.abs(outs[t].astype(np.float32) - frames[t].astype(np.float32))[hole].mean()))
            for t in range(1, n):
                both = (video_inpaint._dilate(masks[t]) | video_inpaint._dilate(masks[t - 1])) & (labels[t] == 0) & (labels[t - 1] == 0)
                if both.sum() < 50:
                    continue
                # 깜빡임 = 결과의 프레임 간 변화 - 원래 영상의 프레임 간 변화 (카메라가 움직이면 원래도 변한다)
                d_out = np.abs(outs[t].astype(np.float32) - outs[t - 1].astype(np.float32))[both].mean()
                d_gt = np.abs(frames[t].astype(np.float32) - frames[t - 1].astype(np.float32))[both].mean()
                flick.append(float(abs(d_out - d_gt)))
            row[f"{key}_l1"] = float(np.mean(l1)) if l1 else None
            row[f"{key}_flicker"] = float(np.mean(flick)) if flick else None
        rows.append(row)
        print(f"  {name:20} {row['mode']:7} 보임 {row['seen_ratio']:.2f} | L1 {row['old_l1']:.1f} → {row['new_l1']:.1f} | "
              f"깜빡임 {row['old_flicker']:.1f} → {row['new_flicker']:.1f} | {t_old:.1f}s → {t_new:.1f}s", flush=True)
    summary = _summary(rows, ("l1", "flicker"), ("old", "new"))
    for mode in ("static", "aligned", "frame"):
        sel = [r for r in rows if r["mode"] == mode]
        if sel:
            summary[f"mode_{mode}"] = {"n": len(sel), **_summary(sel, ("l1", "flicker"), ("old", "new"))}
    return {"rows": rows, "summary": summary}


def _summary(rows, metrics, keys) -> dict:
    rng = np.random.default_rng(0)
    out = {"n": len(rows)}
    a, b = keys
    for m in metrics:
        pairs = [(r[f"{a}_{m}"], r[f"{b}_{m}"]) for r in rows if r.get(f"{a}_{m}") is not None and r.get(f"{b}_{m}") is not None]
        if not pairs:
            continue
        x = np.array(pairs)
        d = x[:, 1] - x[:, 0]
        boots = [rng.choice(d, len(d)).mean() for _ in range(2000)]
        out[m] = {a: float(x[:, 0].mean()), b: float(x[:, 1].mean()),
                  "diff_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["tracking", "removal"])
    ap.add_argument("--n", type=int, default=30, help="removal: 영상 수")
    ap.add_argument("--max-frames", type=int, default=None, help="영상마다 앞에서 이만큼만 (기본 전부)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if not DAVIS.is_dir():
        raise SystemExit(f"DAVIS 없음: {DAVIS} — DAVIS-2017-trainval-480p.zip 을 training/datasets/davis/ 에 푼다")
    report = tracking(args) if args.what == "tracking" else removal(args)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=1))
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
