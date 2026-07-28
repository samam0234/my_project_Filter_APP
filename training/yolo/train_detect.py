#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO object detection 학습 진입점 (Ultralytics).

세그와 별도 탐지 전용. 컷앤킵 Phase 1 서빙은 seg 가 기본이며,
탐지 학습은 데이터셋/실험용으로 유지한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    # -------------------------------------------------------------------------
    # 【수동·CLI】 detect 학습 — 서비스 마스크 본선이 아님 (seg 가 본선)
    # 조건: bbox 라벨 데이터셋 + 사전학습 pt (n 이면 yolo26s.pt 로 변경)
    # 기능: 탐지 mAP 실험. backend Segmentor 에 쓰려면 별도 로드 경로 필요
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Train YOLO detect model")
    parser.add_argument("--model", default="yolo26s.pt", help="사전학습 또는 체크포인트")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "dataset_detect.example.yaml",
    )
    # 【수동·튜닝】 epochs / imgsz / batch
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
