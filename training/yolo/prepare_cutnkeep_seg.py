#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCO-seg 소량셋(coco128-seg)을 컷앤킵 5클래스로 변환한다.

소스: Ultralytics coco128-seg (인스턴스 폴리곤)
타깃 클래스 (backend keywords / dataset_seg.yaml 과 동일):
  0 person  ← COCO person
  1 dog     ← COCO dog
  2 cat     ← COCO cat
  3 car     ← COCO car
  4 bag     ← COCO backpack + handbag + suitcase

사용:
  python training/yolo/prepare_cutnkeep_seg.py
"""

from __future__ import annotations

import argparse
import io
import random
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlopen

# COCO 80 클래스 id → 컷앤킵 5클래스
COCO_TO_CUTNKEEP = {
    0: 0,   # person
    16: 1,  # dog
    15: 2,  # cat
    2: 3,   # car
    24: 4,  # backpack → bag
    26: 4,  # handbag → bag
    28: 4,  # suitcase → bag
}

COCO128_SEG_ZIP = (
    "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128-seg.zip"
)


def _download_zip(url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"download {url}")
    with urlopen(url, timeout=120) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(dest_dir)
    extracted = dest_dir / "coco128-seg"
    if not extracted.is_dir():
        # zip 루트가 한 단계 다를 수 있음
        cands = [p for p in dest_dir.iterdir() if p.is_dir()]
        if not cands:
            raise SystemExit(f"coco128-seg 압축 해제 실패: {dest_dir}")
        extracted = cands[0]
    return extracted


def _remap_label_file(src: Path) -> list[str]:
    lines_out: list[str] = []
    text = src.read_text(encoding="utf-8").strip()
    if not text:
        return lines_out
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) < 7:
            # 세그 폴리곤은 최소 class + 3점(6 좌표)
            continue
        try:
            coco_id = int(float(parts[0]))
        except ValueError:
            continue
        new_id = COCO_TO_CUTNKEEP.get(coco_id)
        if new_id is None:
            continue
        lines_out.append(" ".join([str(new_id), *parts[1:]]))
    return lines_out


def convert(
    src_root: Path,
    dst_root: Path,
    val_ratio: float,
    seed: int,
) -> dict[str, int]:
    img_dir = src_root / "images" / "train2017"
    lbl_dir = src_root / "labels" / "train2017"
    if not img_dir.is_dir() or not lbl_dir.is_dir():
        raise SystemExit(f"coco128-seg 구조 아님: {src_root}")

    pairs: list[tuple[Path, list[str]]] = []
    for img in sorted(img_dir.iterdir()):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        lbl = lbl_dir / f"{img.stem}.txt"
        if not lbl.is_file():
            continue
        mapped = _remap_label_file(lbl)
        if not mapped:
            continue
        pairs.append((img, mapped))

    rng = random.Random(seed)
    rng.shuffle(pairs)
    n_val = max(1, int(round(len(pairs) * val_ratio))) if pairs else 0
    val_set = set(range(n_val))

    for split in ("train", "val"):
        (dst_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (dst_root / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0, "instances": 0}
    for i, (img, mapped) in enumerate(pairs):
        split = "val" if i in val_set else "train"
        shutil.copy2(img, dst_root / "images" / split / img.name)
        (dst_root / "labels" / split / f"{img.stem}.txt").write_text(
            "\n".join(mapped) + "\n",
            encoding="utf-8",
        )
        counts[split] += 1
        counts["instances"] += len(mapped)
    counts["images"] = len(pairs)
    return counts


def write_yaml(yaml_path: Path, data_root: Path) -> None:
    # 커밋용은 yaml 기준 상대 경로. 학습 시 train_segment.resolve_dataset_yaml 이 절대 경로화.
    rel = Path("..") / "datasets" / data_root.name
    yaml_path.write_text(
        (
            "# 컷앤킵 5클래스 세그 (prepare_cutnkeep_seg.py 가 생성)\n"
            "# path 는 yaml 기준 상대. train_segment.py 가 학습 직전에 절대 경로로 해석한다.\n"
            f"path: {rel.as_posix()}\n"
            "train: images/train\n"
            "val: images/val\n"
            "\n"
            "names:\n"
            "  0: person\n"
            "  1: dog\n"
            "  2: cat\n"
            "  3: car\n"
            "  4: bag\n"
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare CutNKeep 5-class seg dataset")
    parser.add_argument(
        "--work",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "datasets",
        help="다운로드·변환 루트",
    )
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="이미 풀어 둔 coco128-seg 만 변환",
    )
    args = parser.parse_args()

    work = args.work
    src = work / "coco128-seg"
    if not args.skip_download or not (src / "images" / "train2017").is_dir():
        src = _download_zip(COCO128_SEG_ZIP, work)

    dst = work / "cutnkeep_seg"
    if dst.exists():
        shutil.rmtree(dst)
    stats = convert(src, dst, val_ratio=args.val_ratio, seed=args.seed)
    yaml_path = Path(__file__).resolve().parents[1] / "configs" / "dataset_seg.yaml"
    write_yaml(yaml_path, dst)

    print("=== cutnkeep_seg ===")
    print(f"images     = {stats.get('images')}")
    print(f"train      = {stats.get('train')}")
    print(f"val        = {stats.get('val')}")
    print(f"instances  = {stats.get('instances')}")
    print(f"out        = {dst}")
    print(f"yaml       = {yaml_path}")
    if stats.get("images", 0) < 8:
        raise SystemExit("변환 이미지가 너무 적습니다. coco128-seg 다운로드를 확인하세요.")


if __name__ == "__main__":
    main()
