#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""학습 best.pt 를 서비스 경로로 복사하고 샘플 1장 추론한다.

사용:
  python training/yolo/apply_best.py
  python training/yolo/apply_best.py --weights training/outputs/segment/cutnkeep_seg/weights/best.pt
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_BEST = (
    Path(__file__).resolve().parents[1] / "outputs" / "segment" / "cutnkeep_seg" / "weights" / "best.pt"
)
DEFAULT_DEST = REPO / "models" / "yolo26s-seg.pt"
VAL_DIR = Path(__file__).resolve().parents[1] / "datasets" / "cutnkeep_seg" / "images" / "val"


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy best.pt to models/ and smoke-predict")
    parser.add_argument("--weights", type=Path, default=DEFAULT_BEST)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--skip-predict", action="store_true")
    args = parser.parse_args()

    if not args.weights.is_file():
        raise SystemExit(f"가중치 없음: {args.weights}")

    args.dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.weights, args.dest)
    print(f"copied {args.weights} -> {args.dest} ({args.dest.stat().st_size} bytes)")
    print("YOLO_MODEL_PATH=models/yolo26s-seg.pt  (backend 재시작)")

    if args.skip_predict:
        return

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("ultralytics 필요 (training venv)") from exc

    image = args.image
    if image is None:
        jpgs = sorted(VAL_DIR.glob("*.jpg"))
        if not jpgs:
            print("val 이미지 없음 — 복사만 완료")
            return
        image = jpgs[0]

    model = YOLO(str(args.dest))
    results = model.predict(str(image), verbose=False)
    names = results[0].names or {}
    labels: list[str] = []
    if results[0].boxes is not None and len(results[0].boxes):
        for cls_id in results[0].boxes.cls.tolist():
            labels.append(str(names.get(int(cls_id), int(cls_id))))
    has_masks = results[0].masks is not None
    print(f"sample  = {image.name}")
    print(f"names   = {names}")
    print(f"labels  = {labels}")
    print(f"masks   = {has_masks}")
    if not has_masks:
        raise SystemExit("세그 마스크가 없습니다. detect 전용 가중치인지 확인하세요.")


if __name__ == "__main__":
    main()
