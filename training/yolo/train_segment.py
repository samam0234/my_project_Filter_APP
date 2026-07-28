#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO 인스턴스 세그멘테이션 학습 진입점 (Ultralytics).

추론(backend)과 분리된 학습 전용 스크립트.
학습 산출 best.pt 를 models/ 로 복사한 뒤 YOLO_MODEL_PATH 로 서빙한다.

사용 예:
  python training/yolo/train_segment.py --data training/configs/dataset_seg.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    # -------------------------------------------------------------------------
    # 【수동·CLI】 학습 하이퍼·경로 — 실행 시 인자로 덮어씀
    # 조건: --data yaml 의 path/names/폴리곤 라벨이 실제 존재
    # 기능: YOLO.train → outputs/segment/<name>/weights/best.pt
    # 이후: best.pt → 루트 models/ 복사 + YOLO_MODEL_PATH (자동 복사 없음·수동)
    # 기본 --model 은 사전학습 체크포인트 이름 (n 쓰려면 yolo26s-seg.pt 로 변경)
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Train YOLO segment model")
    parser.add_argument(
        "--model",
        default="yolo26s-seg.pt",
        help="사전학습 가중치 또는 체크포인트 경로",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "dataset_seg.example.yaml",
        help="데이터셋 yaml",
    )
    # 【수동·튜닝】 epochs / imgsz / batch — VRAM·데이터 양에 맞게
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

    # 학습 전용 의존성 (backend requirements 와 분리)
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
