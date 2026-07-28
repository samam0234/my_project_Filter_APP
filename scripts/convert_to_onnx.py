#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO 세그 가중치(.pt) → ONNX 변환 (Phase 1 추론용).

Ultralytics 로 export 한다. 학습 전용 경로와 동일한 역할은
`training/yolo/export_onnx.py` 에도 있다. 여기 scripts 버전은
운영/빠른 변환용 단축 진입점이다.

사용 예:
  python scripts/convert_to_onnx.py \\
    --weights models/yolo26s-seg.pt \\
    --out models/yolo26s-seg.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLO-seg 가중치를 ONNX 로 내보냄")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path("models/yolov8n-seg.pt"),
        help="원본 .pt 가중치 경로",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("models/yolov8n-seg.onnx"),
        help="목표 ONNX 경로 (안내용; Ultralytics 가 만든 파일을 여기로 옮기면 됨)",
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "ultralytics 가 필요합니다. pip install ultralytics"
        ) from exc

    if not args.weights.exists():
        raise SystemExit(f"가중치 파일을 찾을 수 없습니다: {args.weights}")

    # dynamic=True: 가변 입력 크기 허용 (배포 유연성)
    model = YOLO(str(args.weights))
    model.export(format="onnx", dynamic=True)
    print(f"export 요청 완료: {args.weights} → models/ 아래 .onnx 를 확인하세요")
    print(f"목표 경로(필요 시 수동 이동): {args.out}")
    print("서빙: YOLO_MODEL_PATH 에 .pt 또는 .onnx 경로를 지정한 뒤 backend 재시작")


if __name__ == "__main__":
    main()
