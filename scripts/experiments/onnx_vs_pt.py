#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검증: 직접 구현한 ONNX 추론(onnx_utils.run_yolo_seg_onnx) 이 같은 가중치의 .pt(Ultralytics) 와 얼마나 같은가.

같은 이미지·같은 신뢰도에서
  - 검출 수 일치 (클래스별), 인스턴스를 IoU 로 짝지어 마스크 일치(평균 IoU)
  - 장당 시간 (onnxruntime CPU vs Ultralytics)
  - 정답 폴리곤 대비 검출률 · 위치 선택 정확도 (seg_model_compare.py 와 같은 기준)

준비: .pt 와 같은 모델의 .onnx 를 만든다
  python -c "from ultralytics import YOLO; YOLO('backend/models/yolo26m-seg.pt').export(format='onnx', imgsz=640)"
실행: python scripts/experiments/onnx_vs_pt.py --pt backend/models/yolo26m-seg.pt --onnx backend/models/yolo26m-seg.onnx
결과: docs/plan/ONNX_INFERENCE.md
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import selection_e2e as se  # noqa: E402


def match(a: list, b: list) -> list[float]:
    """a 의 각 마스크를 같은 클래스의 가장 겹치는 b 와 짝지어 IoU 목록 (없으면 0)."""
    used: set[int] = set()
    out = []
    for cls_a, _, m_a in a:
        best, best_j = 0.0, -1
        for j, (cls_b, _, m_b) in enumerate(b):
            if j in used or cls_b != cls_a:
                continue
            v = se.iou(m_a, m_b)
            if v > best:
                best, best_j = v, j
        if best_j >= 0:
            used.add(best_j)
        out.append(best)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", type=Path, default=ROOT / "backend/models/yolo26m-seg.pt")
    ap.add_argument("--onnx", type=Path, default=ROOT / "backend/models/yolo26m-seg.onnx")
    ap.add_argument("--data", type=Path, default=ROOT / "training/datasets/coco_val_sel")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--conf", type=float, default=0.25)
    args = ap.parse_args()

    from ultralytics import YOLO

    from app.services.image_processor import ImageProcessor
    from app.core.config import get_settings
    from app.services.instance_selector import _sort_by_position, select_instances
    from app.services.segmentation import Instance
    from app.utils.image_utils import resize_keep_aspect
    from app.utils.onnx_utils import class_names, create_session, run_yolo_seg_onnx

    settings = get_settings()
    se.DATA = args.data
    processor = ImageProcessor(settings, segmentor=object())
    model = YOLO(str(args.pt))
    sess = create_session(args.onnx)
    names = class_names(sess)
    print(f"ONNX 클래스 이름 {len(names)}개, 입력 {sess.get_inputs()[0].shape}")

    t_pt, t_onnx, ious, count_eq, count_n = [], [], [], 0, 0
    acc = {"pt": Counter(), "onnx": Counter()}
    files = sorted((args.data / "images/val").glob("*.jpg"))[: args.limit]
    for p in files:
        img = cv2.imread(str(p))
        label = args.data / "labels/val" / (p.stem + ".txt")
        if img is None or not label.is_file():
            continue
        prep = processor.preprocess(img)
        t = time.perf_counter()
        # retina_masks=True: 원본 해상도 정밀 마스크 (기본 letterbox 크기 마스크를 단순 확대하면 경계가 거칠어 기준으로 부적절)
        res = model.predict(prep, verbose=False, conf=args.conf, retina_masks=True)[0]
        t_pt.append(time.perf_counter() - t)
        pt = []
        if res.masks is not None:
            for i, m in enumerate(res.masks.data.cpu().numpy()):
                pt.append((int(res.boxes.cls[i]), float(res.boxes.conf[i]), (m > 0.5).astype(np.uint8) * 255))
        t = time.perf_counter()
        ox = run_yolo_seg_onnx(sess, prep, args.conf)
        t_onnx.append(time.perf_counter() - t)

        count_n += 1
        count_eq += int(len(pt) == len(ox))
        ious += match(pt, ox)

        resized, _ = resize_keep_aspect(img, settings.max_image_side)
        shape = resized.shape[:2]
        for cls, gt in se.gt_instances(label, shape).items():
            for key, dets in (("pt", pt), ("onnx", ox)):
                inst = [Instance.from_mask(cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
                                           if m.shape != shape else m, names.get(c, str(c)), s)
                        for c, s, m in dets if names.get(c, str(c)) == cls]
                for g in gt:
                    acc[key]["gt"] += 1
                    acc[key]["found"] += int(any(se.iou(g.mask, q.mask) >= 0.5 for q in inst))
                if len(gt) < 2:
                    continue
                for _, s in se.SCENARIOS:
                    rank = (s.rank or 1) - 1
                    if rank >= len(gt):
                        continue
                    sg = _sort_by_position(list(gt), s.position, shape)
                    if se.is_ambiguous(sg, rank, s.position, shape):
                        continue
                    ch = select_instances(inst, s, resized).chosen if inst else []
                    acc[key]["n"] += 1
                    acc[key]["ok"] += int(bool(ch) and se.iou(ch[0].mask, sg[rank].mask) >= 0.5)

    print(f"\n이미지 {count_n}장 · conf {args.conf}")
    print(f"검출 수 일치 이미지 {100 * count_eq / count_n:.1f}% ({count_eq}/{count_n})")
    print(f"마스크 일치 IoU: 평균 {statistics.mean(ious):.4f} · 중앙값 {statistics.median(ious):.4f} · "
          f"0.9 미만 {sum(v < 0.9 for v in ious)}/{len(ious)} · 짝 없음 {sum(v == 0 for v in ious)}")
    print(f"시간(.pt 는 GPU, onnxruntime 은 CPU 라 직접 비교 불가): Ultralytics {1000 * statistics.mean(t_pt):.0f} ms · onnxruntime {1000 * statistics.mean(t_onnx):.0f} ms (장당 평균)")
    for key in ("pt", "onnx"):
        a = acc[key]
        print(f"{key:<5} 검출률 {100 * a['found'] / a['gt']:.1f}% ({a['found']}/{a['gt']}) · "
              f"선택 {100 * a['ok'] / max(1, a['n']):.1f}% ({a['ok']}/{a['n']})")


if __name__ == "__main__":
    main()
