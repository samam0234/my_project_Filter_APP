#!/usr/bin/env python3
"""Convert YOLOv8/11-seg weights to ONNX for Phase 1 inference."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export YOLO-seg to ONNX")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path("models/yolov8n-seg.pt"),
        help="Source .pt weights",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("models/yolov8n-seg.onnx"),
        help="Output ONNX path",
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "ultralytics required. pip install ultralytics"
        ) from exc

    if not args.weights.exists():
        raise SystemExit(f"Weights not found: {args.weights}")

    model = YOLO(str(args.weights))
    model.export(format="onnx", dynamic=True)
    print(f"Export requested for {args.weights} → check models/ for .onnx")
    print(f"Target path (move if needed): {args.out}")


if __name__ == "__main__":
    main()
