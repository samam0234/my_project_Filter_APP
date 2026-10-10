#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SegFormer(ADE20K 사전학습)를 ONNX 로 내보낸다 — 서비스는 onnxruntime 만 쓴다 (torch·transformers 불필요).

  python scripts/export_stuff_onnx.py --model nvidia/segformer-b2-finetuned-ade-512-512
  → backend/models/segformer-ade.onnx + segformer-ade.labels.json (id → 클래스 이름, 150개)

내보낸 뒤 torch 출력과 숫자가 맞는지 검증한다 (최대 절대 오차 출력). 입력 크기는 모델 기본(b0·b2 512, b5 640).
모델은 크기·정확도 트레이드오프라 docs/vaildates/stuff-segmentation-20261008.md 의 비교표로 고른다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import onnxruntime as ort
    import torch
    from transformers import SegformerForSemanticSegmentation

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="nvidia/segformer-b2-finetuned-ade-512-512")
    ap.add_argument("--size", type=int, default=0, help="입력 한 변 (0 = 모델 이름에서: …-640-640 이면 640, 아니면 512)")
    ap.add_argument("--out", type=Path, default=ROOT / "backend/models/segformer-ade.onnx")
    args = ap.parse_args()
    size = args.size or (640 if "640" in args.model else 512)

    model = SegformerForSemanticSegmentation.from_pretrained(args.model).eval()
    dummy = torch.randn(1, 3, size, size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model, (dummy,), str(args.out), input_names=["pixel_values"], output_names=["logits"],
        opset_version=17, dynamo=False,
    )
    labels = {str(i): n.strip() for i, n in model.config.id2label.items()}
    args.out.with_suffix(".labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=0), encoding="utf-8")

    with torch.no_grad():
        ref = model(pixel_values=dummy).logits.numpy()
    got = ort.InferenceSession(str(args.out), providers=["CPUExecutionProvider"]).run(None, {"pixel_values": dummy.numpy()})[0]
    print(f"{args.out.name}: {args.out.stat().st_size / 1e6:.1f}MB 입력 {size}px 출력 {got.shape} 최대 오차 {np.abs(ref - got).max():.2e}")


if __name__ == "__main__":
    main()
