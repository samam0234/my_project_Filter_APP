#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 마스크 정제(GrabCut) 속도 — 전체 이미지 vs 마스크 주변 영역(ROI)만.

effect_applier 가 요청당 약 2 s 로 세그(0.04 s)보다 훨씬 느려 원인을 잰다.
같은 YOLO 마스크로 두 방식을 돌려 시간 · 두 결과의 일치도 · 정답 폴리곤 대비 IoU 를 비교한다.

실행: python scripts/experiments/refine_speed.py --limit 40
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def iou(a, b):
    a, b = a > 0, b > 0
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 1.0


def gt_person_mask(img_path: Path, shape) -> np.ndarray | None:
    """정답 폴리곤(사람, 클래스 0) 합집합 마스크."""
    label = img_path.parent.parent.parent / "labels" / "val" / (img_path.stem + ".txt")
    if not label.is_file():
        return None
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for line in label.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 7 and parts[0] == "0":
            pts = (np.array(parts[1:], dtype=np.float32).reshape(-1, 2) * [w, h]).astype(np.int32)
            cv2.fillPoly(m, [pts], 255)
    return m if m.any() else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    from app.services import effects
    from app.workflows import nodes

    processor = nodes._get_processor()
    images = sorted((ROOT / "training/datasets/cutnkeep_seg_5k/images/val").glob("*.jpg"))
    t_full, t_roi, ious, sizes = [], [], [], []
    gt_raw, gt_full, gt_roi = [], [], []
    n = 0
    for path in images:
        if n >= args.limit:
            break
        original = cv2.imread(str(path))
        res = processor.segmentor.predict(processor.preprocess(original), targets=["person"])
        if not res.mask.any():
            continue
        mask = cv2.resize(res.mask, (original.shape[1], original.shape[0]), interpolation=cv2.INTER_NEAREST)
        n += 1
        effects.GRABCUT_ROI = False
        t = time.perf_counter(); a = effects.refine_mask(mask, original); t_full.append(time.perf_counter() - t)
        effects.GRABCUT_ROI = True
        t = time.perf_counter(); b = effects.refine_mask(mask, original); t_roi.append(time.perf_counter() - t)
        ious.append(iou(a, b))
        gt = gt_person_mask(path, original.shape[:2])
        if gt is not None:
            gt_raw.append(iou(mask, gt)); gt_full.append(iou(a, gt)); gt_roi.append(iou(b, gt))
        sizes.append(mask.mean() / 255)
    print(f"{n}장 (사람 마스크 면적 중앙값 {100 * statistics.median(sizes):.1f}%)")
    print(f"전체 GrabCut  중앙값 {1000 * statistics.median(t_full):.0f} ms · 최대 {1000 * max(t_full):.0f} ms")
    print(f"ROI  GrabCut  중앙값 {1000 * statistics.median(t_roi):.0f} ms · 최대 {1000 * max(t_roi):.0f} ms")
    print(f"결과 일치 IoU 중앙값 {statistics.median(ious):.3f} · 최소 {min(ious):.3f}")
    if gt_raw:
        print(f"정답 마스크 대비 IoU 평균 ({len(gt_raw)}장): YOLO 원본 {statistics.mean(gt_raw):.3f} · "
              f"전체 GrabCut {statistics.mean(gt_full):.3f} · ROI GrabCut {statistics.mean(gt_roi):.3f}")


if __name__ == "__main__":
    main()
