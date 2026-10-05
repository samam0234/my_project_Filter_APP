#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 실제 이미지에서 "어느 인스턴스" 선택이 정답 인스턴스를 고르는가 (세그 + instance_selector).

프롬프트 해석(LLM)은 빼고, 이미 정답인 selector 를 넣어 **비전 + 선택 규칙**만 잰다.

정답: YOLO 폴리곤 라벨(training/datasets/cutnkeep_seg_5k/labels/val)의 인스턴스 마스크에
      같은 정렬 규칙(왼쪽 = 무게중심 x 등)을 적용해 고른 인스턴스.
예측: 서비스와 같은 전처리 → Segmentor.predict(targets) → select_instances(selector)
판정: 고른 마스크와 정답 마스크 IoU ≥ 0.5 → 정답

오답 원인 분류
  - miss      : 정답 인스턴스를 세그 모델이 아예 못 찾음 (IoU≥0.5 인 예측 없음)
  - order     : 찾았지만 정렬 순서가 다름 (다른 인스턴스 누락·병합·추가 검출 때문)
  - ambiguous : 정답 후보끼리 기준 값 차이가 작아(위치 3%·면적 10% 미만) 사람도 헷갈리는 경우 — 따로 집계

실행 (저장소 루트, training venv):
  python scripts/experiments/selection_e2e.py --limit 600 --report docs/vaildates/selection_e2e.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas.request import InstanceSelector  # noqa: E402
from app.services.instance_selector import _sort_by_position, select_instances  # noqa: E402
from app.services.segmentation import Instance  # noqa: E402

DATA = ROOT / "training" / "datasets" / "cutnkeep_seg_5k"
CLASSES = {0: "person", 1: "dog", 2: "cat", 3: "car"}  # 4: bag 은 COCO handbag/backpack 혼재라 제외
MIN_AREA = 0.01  # 이미지 대비 1% 미만 인스턴스는 정답 후보에서 제외 (군중 속 점 같은 사람)

SCENARIOS = [
    ("왼쪽 첫 번째", InstanceSelector(position="left", count=1)),
    ("왼쪽에서 두 번째", InstanceSelector(position="left", rank=2, count=1)),
    ("오른쪽 첫 번째", InstanceSelector(position="right", count=1)),
    ("가운데", InstanceSelector(position="center", count=1)),
    ("제일 큰", InstanceSelector(position="largest", count=1)),
    ("제일 작은", InstanceSelector(position="smallest", count=1)),
]


def gt_instances(label_file: Path, shape) -> dict[str, list[Instance]]:
    h, w = shape
    out: dict[str, list[Instance]] = defaultdict(list)
    for line in label_file.read_text().splitlines():
        parts = line.split()
        if len(parts) < 7 or int(parts[0]) not in CLASSES:
            continue
        pts = (np.array(parts[1:], dtype=np.float32).reshape(-1, 2) * [w, h]).astype(np.int32)
        mask = np.zeros((h, w), np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        if mask.sum() / 255 < MIN_AREA * h * w:
            continue
        out[CLASSES[int(parts[0])]].append(Instance.from_mask(mask, CLASSES[int(parts[0])], 1.0))
    return out


def iou(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a > 0, b > 0
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 0.0


def _key(inst: Instance, position: str, shape) -> float:
    m = cv2.moments(inst.mask, binaryImage=True)
    cx = m["m10"] / m["m00"] if m["m00"] else 0
    cy = m["m01"] / m["m00"] if m["m00"] else 0
    h, w = shape
    if position in {"left", "right"}:
        return cx / w
    if position == "center":
        return ((cx - w / 2) ** 2 + (cy - h / 2) ** 2) ** 0.5 / max(h, w)
    return inst.area / (h * w)


def is_ambiguous(sorted_gt: list[Instance], idx: int, position: str, shape) -> bool:
    """정답과 이웃 후보의 기준 값 차이가 작으면 애매한 문항."""
    k = _key(sorted_gt[idx], position, shape)
    for j in (idx - 1, idx + 1):
        if 0 <= j < len(sorted_gt):
            other = _key(sorted_gt[j], position, shape)
            if position in {"largest", "smallest"}:
                if abs(k - other) / max(k, other, 1e-9) < 0.10:
                    return True
            elif abs(k - other) < 0.03:
                return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--pred-min-area", type=float, default=0.0,
                    help="예측 인스턴스도 이미지 대비 이 비율 미만이면 빼고 선택 (0 = 서비스 현재 동작)")
    args = ap.parse_args()

    from app.workflows import nodes
    from app.utils.image_utils import resize_keep_aspect

    processor = nodes._get_processor()
    seg = processor.segmentor
    images = sorted((DATA / "images" / "val").glob("*.jpg"))[: args.limit]
    totals = Counter()
    by_scn: dict[str, Counter] = defaultdict(Counter)
    det = Counter()
    examples: list[dict] = []
    started = time.time()

    for img_path in images:
        label = DATA / "labels" / "val" / (img_path.stem + ".txt")
        if not label.is_file():
            continue
        original = cv2.imread(str(img_path))
        if original is None:
            continue
        # 서비스와 같은 입력: 긴 변 축소 + 전처리(CLAHE)
        resized, _ = resize_keep_aspect(original, processor.settings.max_image_side)
        prep = processor.preprocess(original)
        shape = resized.shape[:2]
        gts = gt_instances(label, shape)
        for cls, gt in gts.items():
            if len(gt) < 2:  # 고를 대상이 1개면 선택 문제가 아님
                continue
            pred = seg.predict(prep, targets=[cls]).instances
            pred = [p for p in pred if p.mask.shape == shape] or [
                Instance.from_mask(cv2.resize(p.mask, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST), p.label, p.confidence)
                for p in pred
            ]
            if args.pred_min_area > 0:
                pred = [p for p in pred if p.area >= args.pred_min_area * shape[0] * shape[1]]
            # 검출 재현율 (정답 인스턴스 중 IoU≥0.5 로 찾은 비율)
            for g in gt:
                det["gt"] += 1
                det["found"] += int(any(iou(g.mask, p.mask) >= 0.5 for p in pred))
            for name, sel in SCENARIOS:
                position = sel.position
                rank = (sel.rank or 1) - 1
                if rank >= len(gt):
                    continue
                sorted_gt = _sort_by_position(list(gt), position, shape)
                target = sorted_gt[rank]
                chosen = select_instances(pred, sel, resized).chosen if pred else []
                ok = bool(chosen) and iou(chosen[0].mask, target.mask) >= 0.5
                amb = is_ambiguous(sorted_gt, rank, position, shape)
                bucket = "ambiguous" if amb else "clear"
                c = by_scn[name]
                c[f"{bucket}_n"] += 1
                c[f"{bucket}_ok"] += int(ok)
                totals[f"{bucket}_n"] += 1
                totals[f"{bucket}_ok"] += int(ok)
                if not ok and not amb:
                    found = any(iou(target.mask, p.mask) >= 0.5 for p in pred)
                    cause = "miss" if not found else "order"
                    c[cause] += 1
                    totals[cause] += 1
                    if len(examples) < 40:
                        examples.append({"image": img_path.name, "class": cls, "scenario": name, "cause": cause,
                                         "gt": len(gt), "pred": len(pred)})
        totals["images"] += 1

    def pct(ok, n):
        return f"{100 * ok / n:5.1f}% ({ok}/{n})" if n else "   -  "

    print(f"\n이미지 {totals['images']}장 · {time.time() - started:.0f}s · 검출 재현율(IoU≥0.5, 면적≥1%) "
          f"{pct(det['found'], det['gt'])}")
    print(f"{'시나리오':<12}{'명확한 문항':>22}{'애매한 문항':>22}  오답 원인(명확)")
    for name, _ in SCENARIOS:
        c = by_scn[name]
        print(f"{name:<12}{pct(c['clear_ok'], c['clear_n']):>22}{pct(c['ambiguous_ok'], c['ambiguous_n']):>22}"
              f"  miss {c['miss']} · order {c['order']}")
    print(f"{'전체':<12}{pct(totals['clear_ok'], totals['clear_n']):>22}{pct(totals['ambiguous_ok'], totals['ambiguous_n']):>22}"
          f"  miss {totals['miss']} · order {totals['order']}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "images": totals["images"], "detection": dict(det), "totals": dict(totals),
            "by_scenario": {k: dict(v) for k, v in by_scn.items()}, "examples": examples,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"report → {args.report}")


if __name__ == "__main__":
    main()
