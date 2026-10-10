#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 세그 모델 비교 — 검출률 · 오검출 · 위치/크기 인스턴스 선택 정확도 · 장당 시간.

공정성: 평가 이미지는 **COCO val2017** (어떤 비교 모델도 학습에 쓰지 않음).
  처음 실행 시 COCO 주석(training/datasets/coco_raw/annotations/instances_val2017.json)으로
  같은 클래스(사람·개·고양이·차)가 2개 이상(이미지 1% 이상, crowd 제외)인 장면을 골라
  이미지만 내려받아 YOLO 폴리곤 라벨로 저장한다 (--data, 기본 training/datasets/coco_val_sel — git 무시).
  ※ training/datasets/cutnkeep_seg_5k/val 은 COCO train2017 출신이라 COCO 사전학습 모델이 이미 본 사진 → 비교에 쓰지 말 것

모델: --models 이름=가중치 (쉼표). 기본: 현재 서빙(YOLO_MODEL_PATH) · COCO s · COCO m
선택 정확도는 selection_e2e.py 와 같은 6개 시나리오·판정 (명확한 문항만).

실행: python scripts/experiments/seg_model_compare.py --limit 600
결과: docs/plan/YOLO26M_DEFAULT.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import selection_e2e as se  # noqa: E402

CLS = {"person": 0, "dog": 1, "cat": 2, "car": 3}


def build_coco_val(out: Path, limit: int) -> None:
    """COCO val2017 에서 같은 클래스 2개 이상 장면을 골라 이미지 + YOLO 폴리곤 라벨 저장."""
    ann = ROOT / "training/datasets/coco_raw/annotations/instances_val2017.json"
    coco = json.loads(ann.read_text(encoding="utf-8"))
    cat_name = {c["id"]: c["name"] for c in coco["categories"]}
    imgs = {im["id"]: im for im in coco["images"]}
    per_img = defaultdict(list)
    for a in coco["annotations"]:
        if cat_name[a["category_id"]] in CLS and not a["iscrowd"] and isinstance(a["segmentation"], list):
            per_img[a["image_id"]].append(a)
    chosen = []
    for iid, anns in sorted(per_img.items()):
        area = imgs[iid]["width"] * imgs[iid]["height"]
        counts = Counter(cat_name[a["category_id"]] for a in anns if a["area"] >= 0.01 * area)
        if any(n >= 2 for n in counts.values()):
            chosen.append(iid)
    chosen = chosen[:limit]
    (out / "images/val").mkdir(parents=True, exist_ok=True)
    (out / "labels/val").mkdir(parents=True, exist_ok=True)

    def fetch(iid: int) -> None:
        im = imgs[iid]
        dst = out / "images/val" / im["file_name"]
        if not dst.exists():
            urllib.request.urlretrieve(f"http://images.cocodataset.org/val2017/{im['file_name']}", dst)
        lines = []
        for a in per_img[iid]:
            for poly in a["segmentation"]:
                if len(poly) >= 6:
                    pts = " ".join(f"{poly[i] / im['width']:.6f} {poly[i + 1] / im['height']:.6f}" for i in range(0, len(poly), 2))
                    lines.append(f"{CLS[cat_name[a['category_id']]]} {pts}")
        (out / "labels/val" / (Path(im["file_name"]).stem + ".txt")).write_text("\n".join(lines), encoding="utf-8")

    with ThreadPoolExecutor(16) as ex:
        list(ex.map(fetch, chosen))
    print(f"COCO val2017 평가셋 {len(chosen)}장 → {out}")


def predict(model, image, targets: set[str], threshold: float):
    from app.services.segmentation import Instance

    h, w = image.shape[:2]
    out = []
    for r in model.predict(image, verbose=False, conf=threshold):
        if r.masks is None:
            continue
        for i, m in enumerate(r.masks.data.cpu().numpy()):
            conf = float(r.boxes.conf[i])
            label = str(r.names[int(r.boxes.cls[i])]).lower()
            if label in targets:
                b = (cv2.resize(m, (w, h)) > 0.5).astype(np.uint8) * 255
                if b.any():
                    out.append(Instance.from_mask(b, label, conf))
    return out


def main() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "training/datasets/coco_val_sel")
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--models", default=",".join([
        f"서빙중={settings.yolo_model_file}",
        f"s_coco={ROOT / 'training/yolo26s-seg.pt'}",
        f"m_coco={ROOT / 'backend/models/yolo26m-seg.pt'}",
    ]))
    args = ap.parse_args()
    if not (args.data / "images/val").is_dir():
        build_coco_val(args.data, args.limit)

    from ultralytics import YOLO

    from app.services.instance_selector import _sort_by_position, select_instances
    from app.services.image_processor import ImageProcessor
    from app.utils.image_utils import resize_keep_aspect

    se.DATA = args.data
    processor = ImageProcessor(settings, segmentor=object())  # 전처리만 (세그 모델은 비교 대상만 로드)
    data = []
    for p in sorted((args.data / "images/val").glob("*.jpg"))[: args.limit]:
        label = args.data / "labels/val" / (p.stem + ".txt")
        img = cv2.imread(str(p))
        if img is not None and label.is_file():
            resized, _ = resize_keep_aspect(img, settings.max_image_side)
            data.append((resized, processor.preprocess(img), label))

    print(f"{'모델':<12}{'검출률':>18}{'오검출':>8}{'선택(명확)':>20}{'ms/장':>8}")
    for spec in args.models.split(","):
        name, path = spec.split("=", 1)
        model = YOLO(path)
        det, sel = Counter(), Counter()
        spent = 0.0
        calls = 0
        for resized, prep, label in data:
            shape = resized.shape[:2]
            for cls, gt in se.gt_instances(label, shape).items():
                t = time.perf_counter()
                pred = predict(model, prep, {cls}, settings.min_confidence)
                spent += time.perf_counter() - t
                calls += 1
                for g in gt:
                    det["gt"] += 1
                    det["found"] += int(any(se.iou(g.mask, q.mask) >= 0.5 for q in pred))
                big = [q for q in pred if q.area >= se.MIN_AREA * shape[0] * shape[1]]
                det["fp"] += sum(1 for q in big if not any(se.iou(g.mask, q.mask) >= 0.5 for g in gt))
                if len(gt) < 2:
                    continue
                for _, s in se.SCENARIOS:
                    rank = (s.rank or 1) - 1
                    if rank >= len(gt):
                        continue
                    sg = _sort_by_position(list(gt), s.position, shape)
                    if se.is_ambiguous(sg, rank, s.position, shape):
                        continue
                    chosen = select_instances(pred, s, resized).chosen if pred else []
                    sel["n"] += 1
                    sel["ok"] += int(bool(chosen) and se.iou(chosen[0].mask, sg[rank].mask) >= 0.5)
        print(f"{name:<12}{100 * det['found'] / det['gt']:>9.1f}% ({det['found']}/{det['gt']}){det['fp']:>7}"
              f"{100 * sel['ok'] / max(1, sel['n']):>10.1f}% ({sel['ok']}/{sel['n']}){1000 * spent / max(1, calls):>8.0f}",
              flush=True)


if __name__ == "__main__":
    main()
