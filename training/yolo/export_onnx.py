#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""학습된 YOLO 가중치를 ONNX 로 변환.

Ultralytics export 후 선택적으로 models/ 등 최종 경로로 복사한다.
backend Segmentor 는 .pt 우선, 없으면 .onnx 세션 경로를 시도한다.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export YOLO weights to ONNX")
    parser.add_argument("--weights", type=Path, required=True, help=".pt 경로")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="복사할 최종 onnx 경로 (예: ../models/yolo26n-seg.onnx)",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    if not args.weights.exists():
        raise SystemExit(f"가중치 없음: {args.weights}")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("ultralytics 필요") from exc

    model = YOLO(str(args.weights))
    # dynamic=True: 가변 배치/해상도 입력 허용 (배포 유연성)
    export_path = model.export(format="onnx", imgsz=args.imgsz, dynamic=True)
    export_path = Path(export_path)
    print(f"export 완료: {export_path}")

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(export_path, args.out)
        print(f"복사: {args.out}")
        print("YOLO_MODEL_PATH 에 위 경로를 지정하세요.")


if __name__ == "__main__":
    main()
