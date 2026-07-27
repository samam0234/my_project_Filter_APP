#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO 인스턴스 세그멘테이션 학습 진입점 (Ultralytics)."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLO segment model")
    parser.add_argument(
        "--model",
        default="yolo26n-seg.pt",
        help="사전학습 가중치 또는 체크포인트 경로",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "dataset_seg.example.yaml",
        help="데이터셋 yaml",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "segment",
        help="Ultralytics project 디렉터리",
    )
    parser.add_argument("--name", default="exp", help="run 이름")
    parser.add_argument("--device", default=None, help="cuda:0 또는 cpu (기본 자동)")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "ultralytics 가 필요합니다. "
            "training venv 에서: pip install -r requirements-training.txt"
        ) from exc

    if not args.data.exists():
        raise SystemExit(f"data yaml 없음: {args.data}\n예시 복사 후 path/names 를 수정하세요.")

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

    results = model.train(**kwargs)
    print("학습 완료. best 가중치는 outputs/segment/<name>/weights/best.pt 를 확인하세요.")
    print(results)
    print("적용: models/ 로 복사 후 YOLO_MODEL_PATH 설정 → backend 재시작")


if __name__ == "__main__":
    main()
