#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO object detection 학습 진입점 (Ultralytics)."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLO detect model")
    parser.add_argument("--model", default="yolo26n.pt", help="사전학습 또는 체크포인트")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "dataset_detect.example.yaml",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "detect",
    )
    parser.add_argument("--name", default="exp")
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "ultralytics 필요: pip install -r training/requirements-training.txt"
        ) from exc

    if not args.data.exists():
        raise SystemExit(f"data yaml 없음: {args.data}")

    model = YOLO(args.model)
    kwargs = dict(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(args.project),
        name=args.name,
        exist_ok=True,
    )
    if args.device is not None:
        kwargs["device"] = args.device

    model.train(**kwargs)
    print("탐지 학습 완료. outputs/detect/<name>/weights/best.pt 확인.")


if __name__ == "__main__":
    main()
