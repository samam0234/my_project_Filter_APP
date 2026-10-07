#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: Grounding DINO 박스 임계값 — 대상이 있는 사진에서 잡는 비율(재현율) vs 없는 사진에서 잡는 비율(오검출률).

오픈 보캐브는 "COCO 밖 대상"용이지만 정답 주석이 있는 COCO 클래스를 질의해 점수 분포를 잰다.
이미지마다 클래스 이름 하나로 질의하고 가장 높은 박스 점수를 기록 → 임계값별로
  재현율   = 대상이 있는 (이미지, 클래스) 중 점수 ≥ 임계값 비율
  오검출률 = 대상이 없는 (이미지, 클래스) 중 점수 ≥ 임계값 비율 (없는 것을 지우는 사고)

데이터: training/datasets/coco_val_sel/images/val (seg_model_compare.py 가 만든 COCO val2017 장면)
정답:   training/datasets/coco_raw/annotations/instances_val2017.json
  ※ coco_val_sel/labels 는 프로젝트 4클래스로 재매핑돼 있어 쓰면 안 된다 (사람 외 클래스가 전부 '없음'이 됨)

실행: python scripts/experiments/dino_threshold.py --limit 300 --out docs/vaildates/open_vocab_threshold_20261007.json
결과: docs/vaildates/open-vocab-20261007.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "training/datasets/coco_val_sel/images/val"
ANN = ROOT / "training/datasets/coco_raw/annotations/instances_val2017.json"
CLASSES = ["person", "car", "dog", "backpack", "tie", "bottle", "chair", "tv", "handbag", "umbrella"]
THRESHOLDS = (0.25, 0.3, 0.35, 0.4, 0.45, 0.5)


def main() -> None:
    import torch
    from PIL import Image
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--model", default="IDEA-Research/grounding-dino-tiny")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    ann = json.loads(ANN.read_text(encoding="utf-8"))
    names = {c["id"]: c["name"] for c in ann["categories"]}
    present: dict[int, set[str]] = {}
    for a in ann["annotations"]:
        present.setdefault(a["image_id"], set()).add(names[a["category_id"]])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.model, local_files_only=True).to(device).eval()

    rows = []
    for path in sorted(DATA.glob("*.jpg"))[: args.limit]:
        has = present.get(int(path.stem), set())
        pil = Image.open(path).convert("RGB")
        for name in CLASSES:
            inputs = proc(images=pil, text=f"{name} .", return_tensors="pt").to(device)
            with torch.no_grad():
                out = model(**inputs)
            res = proc.post_process_grounded_object_detection(
                out, inputs.input_ids, threshold=0.05, text_threshold=0.05, target_sizes=[pil.size[::-1]]
            )[0]
            top = float(res["scores"].max()) if len(res["scores"]) else 0.0
            rows.append({"cls": name, "present": name in has, "top": top})

    def rate(subset, th):
        return round(sum(r["top"] >= th for r in subset) / max(len(subset), 1), 3)

    pos = [r for r in rows if r["present"]]
    neg = [r for r in rows if not r["present"]]
    overall = []
    for th in THRESHOLDS:
        tp = sum(r["top"] >= th for r in pos)
        fp = sum(r["top"] >= th for r in neg)
        overall.append({"threshold": th, "recall": rate(pos, th), "false_rate": rate(neg, th),
                        "precision": round(tp / max(tp + fp, 1), 3)})
        print(f"th={th:.2f}  재현율={overall[-1]['recall']:.3f}  오검출률={overall[-1]['false_rate']:.3f}  정밀도={overall[-1]['precision']:.3f}")
    per_class = {}
    for name in CLASSES:
        p = [r for r in pos if r["cls"] == name]
        n = [r for r in neg if r["cls"] == name]
        per_class[name] = {"positives": len(p), "negatives": len(n),
                           "recall": {str(t): rate(p, t) for t in THRESHOLDS},
                           "false_rate": {str(t): rate(n, t) for t in THRESHOLDS}}
    summary = {"model": args.model, "images": args.limit, "pairs": len(rows), "overall": overall, "per_class": per_class}
    if args.out:
        args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
