#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 경계 품질(사진) · 프레임 간 흔들림(영상) — 마스크 후처리 방식별 비교.

사진 (COCO val2017 사람 장면, 정답 = 사람 폴리곤 합집합)
  세그는 서빙과 같게: 긴 변 1280 으로 줄이고 CLAHE → YOLO → 마스크를 원본 크기로 되돌림.
  큰 사진(×3 확대본)도 같이 잰다 — 1280 으로 줄여 세그한 마스크를 원본으로 키우는 과정이 경계를 망치는지 보기 위해.
  방식
    current   : 최근접 확대 → GrabCut 정제 2번 (서빙의 effect_applier 가 정제하고 apply_effects 가 또 정제)
    once      : 최근접 확대 → GrabCut 1번
    linear    : 선형 확대(0.5 임계) → GrabCut 1번
    feather   : linear + 경계 안티앨리어싱 알파 (가우시안, 긴 변의 0.08%) — 서빙 방식
  지표
    IoU, 경계 F (DAVIS 식, 허용 오차 = 대각선의 0.4%, 최소 2px), 부드러운 알파는 soft IoU 도 · 장당 시간

영상 (같은 사진으로 만든 16프레임 클립 — 프레임마다 3px 이동 + JPEG 재압축 + 잡음, 정답 = 이동한 폴리곤)
  방식
    none      : 프레임마다 독립 (현재)
    ema_0.4   : 이전 마스크와 지수 평균, 현재 프레임 비중 0.4 (움직임 보정 없음)
    flow_*    : 광학 흐름(Farneback, 긴 변 320)으로 이전 마스크를 현재 프레임에 맞춰 옮긴 뒤 지수 평균 (비중 0.4 · 0.3)
  지표
    정답 IoU 평균, 흔들림 = 1 − IoU(현재 마스크, 알려진 이동만큼 옮긴 이전 마스크) 평균 — 낮을수록 안정

실행: python scripts/experiments/edge_quality.py --limit 200 --clips 30 --out docs/vaildates/edge_quality_20261008.json
결과: docs/vaildates/edge-tuning-20261008.md
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
DATA = ROOT / "training/datasets/coco_val_sel"


# --------------------------------------------------------------------------- 공통


def gt_mask(label: Path, w: int, h: int) -> np.ndarray:
    """YOLO 폴리곤 라벨에서 사람(0) 합집합."""
    m = np.zeros((h, w), np.uint8)
    for line in label.read_text().splitlines():
        parts = line.split()
        if not parts or parts[0] != "0" or len(parts) < 7:
            continue
        pts = np.array(parts[1:], np.float32).reshape(-1, 2) * [w, h]
        cv2.fillPoly(m, [pts.round().astype(np.int32)], 255)
    return m


def iou(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a > 127, b > 127
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 1.0


def soft_iou(alpha: np.ndarray, gt: np.ndarray) -> float:
    a = alpha.astype(np.float32) / 255.0
    g = (gt > 127).astype(np.float32)
    return float(np.minimum(a, g).sum() / max(np.maximum(a, g).sum(), 1e-6))


def boundary_f(pred: np.ndarray, gt: np.ndarray) -> float:
    h, w = gt.shape[:2]
    tol = max(2, int(round(0.004 * (h * h + w * w) ** 0.5)))
    k3 = np.ones((3, 3), np.uint8)
    kt = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))

    def edge(m):
        b = (m > 127).astype(np.uint8)
        return b - cv2.erode(b, k3)

    bp, bg = edge(pred), edge(gt)
    if bp.sum() == 0 or bg.sum() == 0:
        return 0.0
    precision = (bp & cv2.dilate(bg, kt)).sum() / bp.sum()
    recall = (bg & cv2.dilate(bp, kt)).sum() / bg.sum()
    return float(2 * precision * recall / max(precision + recall, 1e-9))


# --------------------------------------------------------------------------- 사진


def run_photos(seg, processor, limit: int, scales: tuple[int, ...]):
    from app.services.effects import feather_alpha, refine_mask, upscale_mask
    from app.utils.image_utils import resize_keep_aspect

    rows = []
    images = sorted((DATA / "images/val").glob("*.jpg"))
    for path in images:
        if len([r for r in rows if r["scale"] == scales[0]]) >= limit:
            break
        base = cv2.imread(str(path))
        label = DATA / "labels/val" / (path.stem + ".txt")
        if base is None or not label.exists():
            continue
        for scale in scales:
            img = base if scale == 1 else cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            h, w = img.shape[:2]
            gt = gt_mask(label, w, h)
            if gt.mean() / 255 < 0.01:
                break  # 사람이 너무 작은 장면은 경계 비교에서 뺀다
            small, _ = resize_keep_aspect(img, processor.settings.max_image_side)
            res = seg.predict(processor.preprocess(small), targets=["person"])
            if not res.mask.any():
                break
            m_small = res.mask
            out = {"image": path.stem, "scale": scale, "w": w, "h": h}

            t = time.perf_counter()
            near = cv2.resize(m_small, (w, h), interpolation=cv2.INTER_NEAREST)
            cur = refine_mask(refine_mask(near, img), img)
            out["current"] = (iou(cur, gt), boundary_f(cur, gt), time.perf_counter() - t)

            t = time.perf_counter()
            once = refine_mask(near, img)
            out["once"] = (iou(once, gt), boundary_f(once, gt), time.perf_counter() - t)

            t = time.perf_counter()
            lin = refine_mask(upscale_mask(m_small, (w, h)), img)
            out["linear"] = (iou(lin, gt), boundary_f(lin, gt), time.perf_counter() - t)

            t = time.perf_counter()
            alpha = feather_alpha(lin, img)
            dt = time.perf_counter() - t + out["linear"][2]
            hard = np.where(alpha >= 128, 255, 0).astype(np.uint8)
            out["feather"] = (iou(hard, gt), boundary_f(hard, gt), dt, soft_iou(alpha, gt), soft_iou(lin, gt))
            rows.append(out)
    return rows


def summarize_photos(rows, scales):
    summary = {}
    for scale in scales:
        sub = [r for r in rows if r["scale"] == scale]
        if not sub:
            continue
        item = {"images": len(sub)}
        for name in ("current", "once", "linear", "feather"):
            vals = np.array([r[name][:3] for r in sub])
            item[name] = {
                "iou": round(float(vals[:, 0].mean()), 4),
                "boundary_f": round(float(vals[:, 1].mean()), 4),
                "seconds": round(float(vals[:, 2].mean()), 3),
            }
        item["feather"]["soft_iou"] = round(float(np.mean([r["feather"][3] for r in sub])), 4)
        item["feather"]["soft_iou_hard_mask"] = round(float(np.mean([r["feather"][4] for r in sub])), 4)
        summary[f"x{scale}"] = item
    return summary


# --------------------------------------------------------------------------- 영상


def make_clip(img: np.ndarray, gt: np.ndarray, frames: int, step: int, rng):
    h, w = img.shape[:2]
    out = []
    for t in range(frames):
        mat = np.float32([[1, 0, t * step], [0, 1, 0]])
        f = cv2.warpAffine(img, mat, (w, h), borderMode=cv2.BORDER_REPLICATE)
        g = cv2.warpAffine(gt, mat, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
        f = np.clip(f.astype(np.float32) + rng.normal(0, 3, f.shape), 0, 255).astype(np.uint8)
        ok, enc = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(55, 80))])
        out.append((cv2.imdecode(enc, cv2.IMREAD_COLOR), g))
    return out


def shift(mask: np.ndarray, dx: int) -> np.ndarray:
    h, w = mask.shape[:2]
    return cv2.warpAffine(mask, np.float32([[1, 0, dx], [0, 1, 0]]), (w, h), flags=cv2.INTER_NEAREST, borderValue=0)


# (이름, 방식, 현재 프레임 비중) — 이진 마스크라 비중이 0.5 이상이면 현재 프레임이 항상 이겨 효과가 없다
VIDEO_VARIANTS = (
    ("none", None, None),
    ("ema_0.4", "ema", 0.4),
    ("flow_0.4", "flow", 0.4),
    ("flow_0.3", "flow", 0.3),
)


def run_video(seg, clips: int, frames: int = 16, step: int = 3):
    from app.services.video_processor import TemporalSmoother

    rng = np.random.default_rng(0)
    rows = []
    for path in sorted((DATA / "images/val").glob("*.jpg"))[::7]:
        if len(rows) >= clips:
            break
        img = cv2.imread(str(path))
        label = DATA / "labels/val" / (path.stem + ".txt")
        if img is None or not label.exists():
            continue
        gt = gt_mask(label, img.shape[1], img.shape[0])
        if gt.mean() / 255 < 0.03:
            continue
        clip = make_clip(img, gt, frames, step, rng)
        raw = [seg.predict(f, targets=["person"]).mask for f, _ in clip]
        if sum(m.any() for m in raw) < frames // 2:
            continue
        result = {"image": path.stem}
        for name, mode, weight in VIDEO_VARIANTS:
            smoother = TemporalSmoother(mode, weight) if mode else None
            masks, t0 = [], time.perf_counter()
            for (frame, _g), m in zip(clip, raw):
                masks.append(smoother.update(frame, m) if smoother else m)
            dt = (time.perf_counter() - t0) / frames
            acc = float(np.mean([iou(m, g) for m, (_f, g) in zip(masks, clip)]))
            jitter = float(np.mean([1 - iou(masks[t], shift(masks[t - 1], step)) for t in range(1, frames)]))
            result[name] = (acc, jitter, dt)
        rows.append(result)
    return rows


def summarize_video(rows):
    out = {"clips": len(rows)}
    for name, _mode, _weight in VIDEO_VARIANTS:
        vals = np.array([r[name] for r in rows])
        out[name] = {
            "iou": round(float(vals[:, 0].mean()), 4),
            "jitter": round(float(vals[:, 1].mean()), 4),
            "ms_per_frame": round(float(vals[:, 2].mean() * 1000), 2),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--clips", type=int, default=30)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--skip-photos", action="store_true")
    ap.add_argument("--skip-video", action="store_true")
    args = ap.parse_args()

    from app.core.config import get_settings
    from app.services.image_processor import ImageProcessor
    from app.services.segmentation import Segmentor

    settings = get_settings()
    seg = Segmentor(settings)
    processor = ImageProcessor(settings, segmentor=seg)
    result = {"model": settings.yolo_model_file.name}
    scales = (1, 3)
    if not args.skip_photos:
        rows = run_photos(seg, processor, args.limit, scales)
        result["photos"] = summarize_photos(rows, scales)
        print(json.dumps(result["photos"], ensure_ascii=False, indent=1))
    if not args.skip_video:
        vrows = run_video(seg, args.clips)
        result["video"] = summarize_video(vrows)
        print(json.dumps(result["video"], ensure_ascii=False, indent=1))
    if args.out:
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
