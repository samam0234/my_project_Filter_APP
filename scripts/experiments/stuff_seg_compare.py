#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 배경 덩어리(건물·하늘·도로·나무…) 의미 분할 모델 비교 — SegFormer b0 · b2 · b5 (ADE20K 사전학습).

데이터: ADE20K 검증 (HF `zhoubolei/scene_parse_150` parquet, 정답 주석 = 클래스 id 1..150, 0 = 기타)
지표: 서비스가 쓰는 **묶음 클래스**(건물 = building+house+skyscraper+hovel 등)별 IoU · 장당 시간(GPU · CPU) · 파일 크기
  ※ 정답과 예측을 같은 묶음으로 합쳐서 잰다 — 사용자는 "건물" 이라고 말하지 "house" 와 "building" 을 구분하지 않는다

실행: python scripts/experiments/stuff_seg_compare.py --limit 200 --out docs/vaildates/stuff_seg_compare_20261008.json
결과: docs/vaildates/stuff-segmentation-20261008.md
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

MODELS = {
    "b0": "nvidia/segformer-b0-finetuned-ade-512-512",
    "b2": "nvidia/segformer-b2-finetuned-ade-512-512",
    "b5": "nvidia/segformer-b5-finetuned-ade-640-640",
}


def load_samples(limit: int):
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    from PIL import Image

    path = hf_hub_download("zhoubolei/scene_parse_150", "scene_parsing/validation/0000.parquet",
                           repo_type="dataset", revision="refs/convert/parquet")
    rows = pq.ParquetFile(path).read_row_group(0).slice(0, limit).to_pylist()
    out = []
    for row in rows:
        img = np.array(Image.open(io.BytesIO(row["image"]["bytes"])).convert("RGB"))
        ann = np.array(Image.open(io.BytesIO(row["annotation"]["bytes"])))  # 0 = 기타, 1..150
        out.append((img, ann.astype(np.int16) - 1))  # -1 = 기타, 0..149 = 모델 클래스 번호
    return out


def main() -> None:
    import torch
    from transformers import SegformerForSemanticSegmentation

    from app.services.stuff_segmentation import STUFF_GROUPS, group_ids, group_probability, preprocess

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--models", default="b0,b2,b5")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    samples = load_samples(args.limit)
    print(f"ADE20K 검증 {len(samples)}장")
    result = {}
    for key in args.models.split(","):
        model_id = MODELS[key]
        model = SegformerForSemanticSegmentation.from_pretrained(model_id).eval()
        id2label = {int(i): n for i, n in model.config.id2label.items()}
        groups = {g: group_ids(id2label, g) for g in STUFF_GROUPS}
        size = 640 if key == "b5" else 512
        inter = {g: 0 for g in groups}
        union = {g: 0 for g in groups}
        times = {"gpu": [], "cpu": []}
        for device in ("cuda", "cpu"):
            if device == "cuda" and not torch.cuda.is_available():
                continue
            model.to(device)
            subset = samples if device == "cuda" else samples[: max(10, len(samples) // 10)]
            with torch.no_grad():
                for i, (img, ann) in enumerate(subset):
                    x = torch.from_numpy(preprocess(img, size)).to(device)
                    t = time.perf_counter()
                    logits = model(pixel_values=x).logits
                    if device == "cuda":
                        torch.cuda.synchronize()
                    dt = time.perf_counter() - t
                    if i > 0:  # 첫 장은 워밍업
                        times["gpu" if device == "cuda" else "cpu"].append(dt)
                    if device != "cuda":
                        continue
                    low = logits[0].float().cpu().numpy()
                    for g, ids in groups.items():
                        # 서빙(StuffSegmenter.predict)과 같은 규칙: 묶음 확률 합 → 선형 확대 → 0.5 임계
                        p = group_probability(low, ids, img.shape[:2]) >= 0.5
                        a = np.isin(ann, ids)
                        inter[g] += int(np.logical_and(p, a).sum())
                        union[g] += int(np.logical_or(p, a).sum())
            model.to("cpu")
        iou = {g: round(inter[g] / union[g], 4) for g in groups if union[g]}
        result[key] = {
            "model": model_id,
            "params_m": round(sum(p.numel() for p in model.parameters()) / 1e6, 1),
            "input": size,
            "iou": iou,
            "miou_groups": round(float(np.mean(list(iou.values()))), 4),
            "gpu_ms": round(float(np.mean(times["gpu"])) * 1000, 1) if times["gpu"] else None,
            "cpu_ms": round(float(np.mean(times["cpu"])) * 1000, 1) if times["cpu"] else None,
        }
        print(key, json.dumps(result[key], ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps({"images": len(samples), "models": result}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
