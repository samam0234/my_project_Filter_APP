#!/usr/bin/env python3
"""영상 · GIF 에서 고른 대상 따라가기 — 프레임마다 selector 다시 적용 vs 처음 고른 인스턴스 추적.

정답이 있는 합성 영상: 사람이 없는 COCO 사진을 배경으로, 다른 사진의 사람 두 명(A · B)을 잘라 붙여
A 는 왼쪽 → 오른쪽, B 는 오른쪽 → 왼쪽으로 걸어 **가운데에서 서로 지나가게** 한다 (절반은 A 가 앞, 절반은 B 가 앞 — 뒤쪽은 가려진다).
프롬프트 "왼쪽 사람"(position=left) 의 대상은 첫 프레임에서 왼쪽인 A. 오른쪽(position=right) 도 같은 방식으로 B.

지표 (프레임마다 결과 마스크가 정답 대상과 다른 사람 중 어느 쪽과 더 겹치는지)
  correct : 대상과 더 겹친 프레임 비율 (대상이 거의 다 가려진 프레임은 뺀다)
  after   : 지나간 뒤(후반 1/3) 프레임만의 correct — 프레임마다 다시 고르면 여기서 다른 사람으로 바뀐다
  iou     : 대상 정답과의 평균 IoU

세그: --seg oracle (정답 마스크를 인스턴스로 — 추적 논리만), --seg yolo (실제 모델, 붙여 넣은 사람을 검출)
실행: python scripts/experiments/video_tracking_eval.py --n 40 --seg oracle --out docs/vaildates/video_tracking_eval_oracle_20261009.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

from app.schemas.request import InstanceSelector, ParsedPrompt  # noqa: E402
from app.services.segmentation import Instance, SegmentationResult  # noqa: E402
from app.services.video_processor import FrameRenderer  # noqa: E402

FRAMES = 24
SIDE = 480
HIDDEN = 0.15  # 대상이 원래 크기의 이 비율 미만만 보이면 그 프레임은 채점에서 뺀다


def cut(img, mask, height):
    ys, xs = np.nonzero(mask)
    m = mask[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1].astype(np.uint8)
    i = img[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]
    s = height / m.shape[0]
    size = (max(4, int(m.shape[1] * s)), height)
    return cv2.resize(i, size, interpolation=cv2.INTER_AREA), cv2.resize(m, size, interpolation=cv2.INTER_NEAREST) > 0


def make_clip(bg, a, b, a_front: bool, rng):
    """(frames, 보이는 A 마스크들, 보이는 B 마스크들)."""
    h, w = bg.shape[:2]
    (ai, am), (bi, bm) = a, b
    ya, yb = h - am.shape[0] - 1 - int(rng.integers(0, 12)), h - bm.shape[0] - 1 - int(rng.integers(0, 12))
    frames, vis_a, vis_b = [], [], []
    for t in range(FRAMES):
        f = t / (FRAMES - 1)
        xa = int((w - am.shape[1]) * (0.05 + 0.9 * f))
        xb = int((w - bm.shape[1]) * (0.95 - 0.9 * f))
        frame = bg.copy()
        full_a, full_b = np.zeros((h, w), bool), np.zeros((h, w), bool)
        full_a[ya: ya + am.shape[0], xa: xa + am.shape[1]] = am
        full_b[yb: yb + bm.shape[0], xb: xb + bm.shape[1]] = bm
        order = [("b", bi, bm, xb, yb), ("a", ai, am, xa, ya)] if a_front else [("a", ai, am, xa, ya), ("b", bi, bm, xb, yb)]
        for _name, ii, mm, x, y in order:
            region = frame[y: y + mm.shape[0], x: x + mm.shape[1]]
            region[mm] = ii[mm]
        if a_front:
            full_b &= ~full_a
        else:
            full_a &= ~full_b
        frames.append(frame)
        vis_a.append(full_a)
        vis_b.append(full_b)
    return frames, vis_a, vis_b


class OracleSeg:
    """정답 보이는 마스크를 인스턴스로 (순서는 섞는다). 너무 작게 보이면 검출 실패로 친다."""

    def __init__(self, masks, rng):
        self.masks = iter(masks)
        self.rng = rng

    def predict(self, frame, targets=None):
        items = []
        for m in next(self.masks):
            if m.sum() > 0.01 * m.size:
                items.append(Instance.from_mask(m.astype(np.uint8) * 255, "person", 0.9))
        self.rng.shuffle(items)
        union = np.zeros(frame.shape[:2], np.uint8)
        for i in items:
            union |= i.mask
        return SegmentationResult(mask=union, instances=items, labels=["person"] * len(items), backend="oracle")


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 0.0


def run(frames, vis, target, other, position, seg_factory, track):
    parsed = ParsedPrompt(target=["person"], effect="remove_bg", selector=InstanceSelector(position=position))
    renderer = FrameRenderer(parsed, seg_factory(), smoothing="off", track=track)
    full = max(v.sum() for v in target)
    ok, ious, after = [], [], []
    for t, frame in enumerate(frames):
        m = renderer.mask(frame) > 127
        if target[t].sum() < HIDDEN * full:
            continue
        good = iou(m, target[t]) >= iou(m, other[t]) and m.any()
        ok.append(good)
        ious.append(iou(m, target[t]))
        if t >= FRAMES * 2 // 3:
            after.append(good)
    return {"correct": float(np.mean(ok)), "after": float(np.mean(after)) if after else None, "iou": float(np.mean(ious)),
            "reselected": renderer.tracker.reselected if renderer.tracker else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--reps", type=int, default=3, help="배경 한 장에 만들 사람 조합 수")
    ap.add_argument("--seg", choices=["oracle", "yolo"], default="oracle")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    import leak_eval as L

    yolo = None
    if args.seg == "yolo":
        from app.core.config import Settings
        from app.services.segmentation import Segmentor

        yolo = Segmentor(Settings.model_validate({"DB_DIALECT": "sqlite", "PRELOAD_MODELS": False, "SEG_PREFER_ONNX": False}))

    pool = L.load_gt()
    rng = np.random.default_rng(3)
    persons = [(gt, i) for gt in pool for i in gt.instances
               if i["cat"] == "person" and i["area"] > 0.04 * gt.shape[0] * gt.shape[1] and not i.get("crowd")]
    rows = []
    for gt in pool:
        if len(rows) >= args.n * 2:
            break
        bg = cv2.imread(str(gt.path))
        if bg is None or any(i["cat"] == "person" for i in gt.instances):
            continue
        s = SIDE / max(bg.shape[:2])
        bg = cv2.resize(bg, (int(bg.shape[1] * s), int(bg.shape[0] * s)), interpolation=cv2.INTER_AREA)
        h = bg.shape[0]
        for _rep in range(args.reps):
            picks = rng.choice(len(persons), 2, replace=False)
            donors = []
            for k in picks:
                dgt, inst = persons[int(k)]
                donors.append(cut(cv2.imread(str(dgt.path)), inst["mask"], int(h * rng.uniform(0.55, 0.8))))
            if max(d[1].shape[1] for d in donors) > bg.shape[1] * 0.4:
                continue
            a_front = len(rows) % 4 < 2
            frames, va, vb = make_clip(bg, donors[0], donors[1], a_front, rng)
            for position, target, other in (("left", va, vb), ("right", vb, va)):
                row = {"image": gt.path.name, "position": position, "a_front": a_front}
                for track in (False, True):
                    if yolo is not None:
                        factory = lambda: yolo  # noqa: E731
                    else:
                        factory = lambda: OracleSeg(list(zip(va, vb)), np.random.default_rng(len(rows)))  # noqa: E731
                    res = run(frames, None, target, other, position, factory, track)
                    row.update({f"{'track' if track else 'frame'}_{k}": v for k, v in res.items()})
                rows.append(row)

    rng2 = np.random.default_rng(0)
    summary = {"n": len(rows), "seg": args.seg}
    for k in ("correct", "after", "iou"):
        old = np.array([r[f"frame_{k}"] for r in rows if r[f"frame_{k}"] is not None])
        new = np.array([r[f"track_{k}"] for r in rows if r[f"track_{k}"] is not None])
        d = new - old
        boots = [rng2.choice(d, len(d)).mean() for _ in range(2000)]
        summary[k] = {"frame": float(old.mean()), "track": float(new.mean()),
                      "diff_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
    summary["track_reselected_mean"] = float(np.mean([r["track_reselected"] for r in rows]))
    print(f"seg={args.seg} n={len(rows)} (클립 {len(rows) // 2}개 × 왼쪽/오른쪽)")
    for k in ("correct", "after", "iou"):
        v = summary[k]
        print(f"  {k:8} 프레임마다 {v['frame']:.3f} → 추적 {v['track']:.3f}  차이 95% CI {np.round(v['diff_ci95'], 3)}")
    print(f"  추적 중 selector 로 다시 고른 횟수 평균 {summary['track_reselected_mean']:.2f} (처음 1회 포함)")
    if args.out:
        args.out.write_text(json.dumps({"frames": FRAMES, "side": SIDE, "summary": summary, "rows": rows},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
