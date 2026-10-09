#!/usr/bin/env python3
"""GIF 배경 제거 경계 — 매트(밝은 · 어두운 배경색과 미리 섞기) 효과.

COCO 정답 사람 마스크로 실제 배경 제거 결과(부드러운 경계의 RGBA)를 만들고, GIF 로 저장했다 다시 읽어
흰 배경 · 어두운 배경 위에 올린 모습을 **이상적인 합성(RGBA 를 그 배경에 알파 합성)** 과 비교한다. 경계 띠(알파 0~255 사이 + 3px)만 잰다.

  none  : 지금까지 — 알파 128 미만은 투명, 나머지는 원래 색 (계단 · 배경에 따라 헤일로)
  light : 흰색과 미리 섞음 (밝은 배경용)
  dark  : 어두운 색과 미리 섞음 (어두운 배경용)

실행: python scripts/experiments/gif_matte_eval.py --n 30 --out docs/vaildates/gif_matte_eval_20261009.json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

from app.schemas.request import ParsedPrompt  # noqa: E402
from app.services.effects import apply_effects  # noqa: E402
from app.services.gif_processor import MATTES, encode_gif  # noqa: E402

BACKGROUNDS = {"light": (255, 255, 255), "dark": (15, 23, 42)}


def composite(rgb: np.ndarray, alpha: np.ndarray, bg: tuple[int, int, int]) -> np.ndarray:
    a = alpha.astype(np.float32)[..., None] / 255.0
    return rgb.astype(np.float32) * a + np.array(bg, np.float32) * (1 - a)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    import leak_eval as L

    rows = []
    for gt in L.load_gt():
        if len(rows) >= args.n:
            break
        persons = [i for i in gt.instances if i["cat"] == "person" and i["area"] > 0.05 * gt.shape[0] * gt.shape[1]]
        if not persons:
            continue
        img = cv2.imread(str(gt.path))
        mask = (persons[0]["mask"].astype(np.uint8) * 255)
        bgra = apply_effects(img, mask, ParsedPrompt(target=["person"], effect="remove_bg"), refine=False)
        rgb = cv2.cvtColor(bgra[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = bgra[:, :, 3]
        soft = (alpha > 0) & (alpha < 255)
        band = cv2.dilate(soft.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        row = {"image": gt.path.name, "edge_px": int(band.sum())}
        for matte in ("none", "light", "dark"):
            data = encode_gif([bgra], [100], 0, True, MATTES.get(matte))
            frame = np.array(Image.open(io.BytesIO(data)).convert("RGBA"))
            for bg_name, bg in BACKGROUNDS.items():
                ideal = composite(rgb, alpha, bg)
                shown = composite(frame[:, :, :3], frame[:, :, 3], bg)
                row[f"{matte}_on_{bg_name}"] = float(np.abs(shown - ideal)[band].mean())
        rows.append(row)

    summary = {}
    for matte in ("none", "light", "dark"):
        for bg_name in BACKGROUNDS:
            key = f"{matte}_on_{bg_name}"
            summary[key] = float(np.mean([r[key] for r in rows]))
    print(f"n={len(rows)} (경계 띠 L1, 낮을수록 이상적인 합성과 같음)")
    for bg_name in BACKGROUNDS:
        print(f"  {bg_name:5} 배경: none {summary[f'none_on_{bg_name}']:.1f} | light {summary[f'light_on_{bg_name}']:.1f} | dark {summary[f'dark_on_{bg_name}']:.1f}")
    if args.out:
        args.out.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
