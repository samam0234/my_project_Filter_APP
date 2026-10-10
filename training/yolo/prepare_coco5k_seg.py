#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCO train2017 에서 컷앤킵 5클래스 ~5000장을 골라 YOLO-seg + LoRA JSON 을 만든다.

품질:
  - 공식 COCO 인스턴스 폴리곤 (iscrowd 제외)
  - 너무 작은 인스턴스(면적 < 32^2) 제외
  - dog/cat/bag/car 를 먼저 채워 사람만 가득한 셋이 되지 않게 함

사용:
  python training/yolo/prepare_coco5k_seg.py --limit 5000
"""

from __future__ import annotations

import argparse
import io
import json
import random
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

ANN_ZIP = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
IMG_URL = "http://images.cocodataset.org/train2017/{stem}.jpg"

# COCO category **name** → 컷앤킵 id (JSON category_id 숫자와 혼동 금지)
NAME_TO_CK = {
    "person": 0,
    "dog": 1,
    "cat": 2,
    "car": 3,
    "backpack": 4,
    "handbag": 4,
    "suitcase": 4,
}
CK_NAMES = {0: "person", 1: "dog", 2: "cat", 3: "car", 4: "bag"}
KO = {
    "person": "사람",
    "dog": "강아지",
    "cat": "고양이",
    "car": "자동차",
    "bag": "가방",
}
EFFECTS = [
    ("remove_bg", "만 남기고 배경 제거", False, 15),
    ("blur", "만 남기고 배경 블러", False, 20),
    ("crop", "만 크롭", True, 15),
]


def _get(url: str, timeout: int = 60) -> bytes:
    req = Request(url, headers={"User-Agent": "CutNKeep-coco5k/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def download_annotations(raw_dir: Path) -> Path:
    inst = raw_dir / "annotations" / "instances_train2017.json"
    if inst.is_file() and inst.stat().st_size > 100_000_000:
        print(f"annotations cached: {inst}")
        return inst
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / "annotations_trainval2017.zip"
    if not zip_path.is_file():
        print(f"download {ANN_ZIP}")
        zip_path.write_bytes(_get(ANN_ZIP, timeout=300))
    print(f"extract {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(raw_dir)
    if not inst.is_file():
        raise SystemExit(f"instances_train2017.json 없음: {raw_dir}")
    return inst


def coco_to_yolo_polys(
    anns: list[dict],
    cat_to_ck: dict[int, int],
    width: int,
    height: int,
    min_area: float,
) -> list[str]:
    lines: list[str] = []
    if width < 1 or height < 1:
        return lines
    for ann in anns:
        if ann.get("iscrowd"):
            continue
        ck = cat_to_ck.get(int(ann["category_id"]))
        if ck is None:
            continue
        if float(ann.get("area") or 0) < min_area:
            continue
        seg = ann.get("segmentation")
        if not isinstance(seg, list):
            continue
        for poly in seg:
            if not isinstance(poly, list) or len(poly) < 6:
                continue
            xs = [max(0.0, min(1.0, float(poly[i]) / width)) for i in range(0, len(poly), 2)]
            ys = [max(0.0, min(1.0, float(poly[i]) / height)) for i in range(1, len(poly), 2)]
            if len(xs) < 3:
                continue
            coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in zip(xs, ys))
            lines.append(f"{ck} {coords}")
    return lines


def sample_images(
    coco: dict,
    cat_to_ck: dict[int, int],
    limit: int,
    min_area: float,
    seed: int,
) -> list[dict]:
    anns_by_img: dict[int, list[dict]] = defaultdict(list)
    for ann in coco["annotations"]:
        anns_by_img[int(ann["image_id"])].append(ann)

    by_ck: dict[int, list[dict]] = defaultdict(list)
    for img in coco["images"]:
        lines = coco_to_yolo_polys(
            anns_by_img.get(int(img["id"]), []),
            cat_to_ck,
            int(img["width"]),
            int(img["height"]),
            min_area,
        )
        if not lines:
            continue
        rec = {**img, "_lines": lines}
        present = {int(ln.split()[0]) for ln in lines}
        for ck in present:
            by_ck[ck].append(rec)

    rng = random.Random(seed)
    for ck in by_ck:
        rng.shuffle(by_ck[ck])

    # 희귀 클래스 쿼터를 먼저 채운 뒤 person 으로 5000 맞춤
    quotas = {1: 900, 2: 900, 4: 900, 3: 1100, 0: 10_000}
    selected: list[dict] = []
    seen: set[int] = set()
    added_for: dict[int, int] = defaultdict(int)
    for ck in (1, 2, 4, 3, 0):
        for rec in by_ck.get(ck, []):
            if len(selected) >= limit:
                return selected[:limit]
            iid = int(rec["id"])
            if iid in seen:
                continue
            if added_for[ck] >= quotas[ck]:
                break
            selected.append(rec)
            seen.add(iid)
            added_for[ck] += 1
    return selected[:limit]


def _download_one(stem: str, dest: Path) -> tuple[str, bool, str]:
    if dest.is_file() and dest.stat().st_size > 1000:
        return stem, True, "cached"
    url = IMG_URL.format(stem=stem)
    try:
        dest.write_bytes(_get(url, timeout=30))
        return stem, True, "ok"
    except Exception as exc:
        if dest.exists():
            dest.unlink()
        return stem, False, str(exc)


def write_lora_json(pseudo_dir: Path, stem: str, class_ids: list[int], rng: random.Random) -> None:
    unique = []
    for cid in class_ids:
        name = CK_NAMES[cid]
        if name not in unique:
            unique.append(name)
    if not unique:
        return
    effect, suffix, crop, intensity = rng.choice(EFFECTS)
    if len(unique) == 1:
        ko = KO[unique[0]]
        prompt = f"{ko}{suffix}"
    else:
        ko_join = "와 ".join(KO[n] for n in unique)
        prompt = f"{ko_join}{suffix}"
    payload = {
        "case_id": f"coco_{stem}",
        "vote": "like",
        "source": "pseudo",
        "prompt": prompt,
        "parsed_prompt": {
            "target": unique,
            "effect": effect,
            "intensity": intensity,
            "crop": crop,
        },
        "meta": {
            "prompt": prompt,
            "parsed_prompt": {
                "target": unique,
                "effect": effect,
                "intensity": intensity,
                "crop": crop,
            },
            "source": "pseudo",
        },
        "image": f"{stem}.jpg",
    }
    (pseudo_dir / f"coco_{stem}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_yaml(yaml_path: Path, data_root: Path) -> None:
    rel = Path("..") / "datasets" / data_root.name
    yaml_path.write_text(
        (
            "# 컷앤킵 5클래스 세그 ~5k (prepare_coco5k_seg.py)\n"
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
    parser = argparse.ArgumentParser(description="Prepare ~5000 COCO images for CutNKeep seg + LoRA")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--val-ratio", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-area", type=float, default=1024.0)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument(
        "--work",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "datasets",
    )
    parser.add_argument(
        "--pseudo-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "pseudo_labels",
    )
    args = parser.parse_args()

    raw = args.work / "coco_raw"
    inst = download_annotations(raw)
    print(f"load {inst} ...")
    coco = json.loads(inst.read_text(encoding="utf-8"))
    cat_to_ck: dict[int, int] = {}
    for cat in coco["categories"]:
        ck = NAME_TO_CK.get(str(cat.get("name") or ""))
        if ck is not None:
            cat_to_ck[int(cat["id"])] = ck
    print(f"mapped coco cats: {cat_to_ck}")

    picked = sample_images(coco, cat_to_ck, args.limit, args.min_area, args.seed)
    print(f"sampled images = {len(picked)}")
    if len(picked) < max(100, args.limit // 10):
        raise SystemExit("샘플이 너무 적습니다. annotations 를 확인하세요.")

    rng = random.Random(args.seed)
    rng.shuffle(picked)
    n_val = max(1, int(round(len(picked) * args.val_ratio)))
    dst = args.work / "cutnkeep_seg_5k"
    for split in ("train", "val"):
        (dst / "images" / split).mkdir(parents=True, exist_ok=True)
        (dst / "labels" / split).mkdir(parents=True, exist_ok=True)
    args.pseudo_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    meta = []
    for i, rec in enumerate(picked):
        split = "val" if i < n_val else "train"
        stem = f"{int(rec['id']):012d}"
        img_path = dst / "images" / split / f"{stem}.jpg"
        lbl_path = dst / "labels" / split / f"{stem}.txt"
        lbl_path.write_text("\n".join(rec["_lines"]) + "\n", encoding="utf-8")
        class_ids = [int(ln.split()[0]) for ln in rec["_lines"]]
        write_lora_json(args.pseudo_dir, stem, class_ids, rng)
        jobs.append((stem, img_path))
        meta.append(split)

    ok = fail = 0
    print(f"download {len(jobs)} jpegs workers={args.workers}")
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = [pool.submit(_download_one, stem, path) for stem, path in jobs]
        for n, fut in enumerate(as_completed(futs), 1):
            stem, success, msg = fut.result()
            if success:
                ok += 1
            else:
                fail += 1
                print(f"fail {stem}: {msg}")
            if n % 250 == 0 or n == len(futs):
                print(f"  images {n}/{len(futs)} ok={ok} fail={fail}")

    # 실패한 이미지는 라벨/JSON 정리
    if fail:
        for stem, img_path in jobs:
            if not img_path.is_file():
                img_path.with_suffix(".jpg")
                lbl = img_path.parent.parent.parent / "labels" / img_path.parent.name / f"{stem}.txt"
                if lbl.is_file():
                    lbl.unlink()
                js = args.pseudo_dir / f"coco_{stem}.json"
                if js.is_file():
                    js.unlink()

    yaml_path = Path(__file__).resolve().parents[1] / "configs" / "dataset_seg.yaml"
    write_yaml(yaml_path, dst)
    train_n = sum(1 for s in meta if s == "train")
    val_n = sum(1 for s in meta if s == "val")
    print("=== cutnkeep_seg_5k ===")
    print(f"sampled  = {len(picked)}")
    print(f"train    = {train_n}")
    print(f"val      = {val_n}")
    print(f"downloaded_ok = {ok} fail={fail}")
    print(f"out      = {dst}")
    print(f"yaml     = {yaml_path}")
    print(f"lora json= {args.pseudo_dir}")
    if ok < args.limit * 0.8:
        raise SystemExit("다운로드 성공 이미지가 목표의 80% 미만입니다.")


if __name__ == "__main__":
    main()
