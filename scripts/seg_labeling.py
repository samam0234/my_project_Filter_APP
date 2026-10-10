#!/usr/bin/env python3
"""세그 모델 개선용 라벨링 — 서비스에서 실패 · 확신 낮았던 사진 → 초벌 라벨 → 사람이 고침 → 검사 → 재학습 데이터.

서비스 모델은 이미 COCO 로 학습돼 COCO 사진으로는 나아지지 않는다 (docs/vaildates/yolo-retrain-20261009.md).
필요한 것은 **서비스에서 틀린 실제 사진**이다. 이 스크립트는 그 사진을 사람이 라벨링하기 쉽게 만든다.

  export    data/feedback 의 사례(파이프라인 실패 · 확신 낮음(HARD_EXAMPLE_CONF) · 사용자가 싫어요 누른 것) 중 이미지가 있는 것을 모아
            큰 모델(yolo26x-seg)로 초벌 폴리곤을 붙인다. 출력 폴더:
              images/            원본 사진
              labels/            초벌 YOLO-seg 라벨 (80클래스, 서비스 모델 순서)
              labelstudio.json   Label Studio 가져오기용 (초벌 = predictions, 사람이 고쳐서 제출)
              classes.txt        모델 클래스 순서 (라벨 번호의 기준)
              cases.json         사진마다 원래 요청 문장 · 해석 · 실패 이유 (라벨러가 무엇이 틀렸는지 보도록)
              README.md          작업 순서
  check     사람이 고친 YOLO-seg 폴더(images/ labels/)를 학습 전에 검사 — 라벨 없는 사진 · 잘못된 클래스 번호 · 점 3개 미만
            폴리곤 · 0~1 밖 좌표 · 라벨링 도구가 클래스 순서를 바꿔 내보냈는지(classes.txt, --fix 로 모델 순서에 맞춤). 문제가 없으면 `scripts/retrain_yolo.py --extra <폴더>` 로 넣으면 된다

개인정보: 회원 사진이다. 출력은 git 밖(training/datasets/**)에 두고, 외부 라벨링 서비스로 보내지 않는다 (로컬 Label Studio 권장).
실행: python scripts/seg_labeling.py export --out training/datasets/seg_review/261009
      python scripts/seg_labeling.py check training/datasets/seg_review/261009_fixed
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "training" / "lora"))

DEFAULT_MODEL = ROOT / "backend/models/yolo26x-seg.pt"
PROMPT_SOURCES = {"pipeline_failure"}  # 자동 수집 (실패 · 확신 낮음)


def pick_cases(feedback_dir: Path, include_likes: bool = False) -> list:
    """이미지가 있고 세그를 다시 볼 가치가 있는 사례 — 파이프라인 실패 · 확신 낮음 · 싫어요."""
    from dataset import discover_feedback_cases

    out = []
    for case in discover_feedback_cases(feedback_dir):
        if case.image_path is None or not Path(case.image_path).is_file():
            continue
        if case.source in PROMPT_SOURCES or case.vote == "dislike" or (include_likes and case.vote == "like"):
            out.append(case)
    return out


def _polygons(result, min_points: int = 3) -> list[tuple[int, np.ndarray]]:
    """ultralytics 결과 → [(클래스, 정규화 폴리곤 Nx2)]."""
    if result.masks is None:
        return []
    out = []
    for cls, poly in zip(result.boxes.cls.tolist(), result.masks.xyn):
        if len(poly) >= min_points:
            out.append((int(cls), np.asarray(poly, np.float32)))
    return out


def export(args) -> int:
    from ultralytics import YOLO

    cases = pick_cases(args.feedback_dir, args.include_likes)
    if not cases:
        print(f"내보낼 사례가 없습니다 ({args.feedback_dir}). HARD_EXAMPLE_CONF 를 켜거나 사용자 싫어요가 쌓이면 다시 실행하세요.")
        return 0
    out: Path = args.out
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)
    model = YOLO(str(args.model))
    names = model.names
    tasks, meta = [], []
    for case in cases:
        src = Path(case.image_path)
        dst = out / "images" / f"{case.case_id}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        res = model.predict(str(dst), imgsz=args.imgsz, conf=args.conf, retina_masks=True, verbose=False, device=args.device)[0]
        h, w = res.orig_shape
        polys = _polygons(res)
        (out / "labels" / f"{dst.stem}.txt").write_text(
            "".join(f"{c} " + " ".join(f"{v:.5f}" for v in p.reshape(-1)) + "\n" for c, p in polys), encoding="utf-8")
        tasks.append({
            "data": {"image": f"/data/local-files/?d=images/{dst.name}", "case_id": case.case_id, "prompt": case.prompt or ""},
            "predictions": [{
                "model_version": Path(args.model).name,
                "result": [{
                    "type": "polygonlabels", "from_name": "label", "to_name": "image",
                    "original_width": w, "original_height": h, "image_rotation": 0,
                    "value": {"points": (p * 100).round(2).tolist(), "polygonlabels": [names[c]]},
                } for c, p in polys],
            }],
        })
        payload_meta = (case.payload or {}).get("meta") or {}
        meta.append({"case_id": case.case_id, "image": dst.name, "vote": case.vote, "source": case.source,
                     "prompt": case.prompt, "parsed_prompt": case.parsed_prompt, "comment": case.comment,
                     "hard_example": payload_meta.get("hard_example"), "error": payload_meta.get("error"),
                     "labels_detected": payload_meta.get("labels"), "prelabels": len(polys)})
        print(f"  {dst.name}: 초벌 {len(polys)}개 · {case.source}/{case.vote} · {case.prompt or ''}")
    (out / "labelstudio.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "classes.txt").write_text("".join(f"{n}\n" for _, n in sorted(names.items())), encoding="utf-8")  # 모델 클래스 순서
    (out / "cases.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    label_config = "\n".join(f'    <Label value="{n}"/>' for _, n in sorted(names.items()))
    (out / "README.md").write_text(f"""# 세그 라벨링 묶음 ({len(cases)}장)

초벌 라벨: `{Path(args.model).name}` (conf {args.conf}) — **사람이 고쳐야 정답이 된다.** 특히 맞닿은 사람의 경계,
한 사람으로 합쳐진 두 사람, 빠진 사람을 고친다. 무엇이 틀렸었는지는 `cases.json` 의 요청 문장 · 실패 이유를 본다.

## Label Studio (로컬)

1. `pip install label-studio` → `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT={out.resolve().as_posix()} label-studio`
2. 프로젝트 만들기 → Labeling Interface 에 아래 설정 → Import 에 `labelstudio.json`
3. 고친 뒤 Export → **YOLO with Images** (폴리곤) → 압축을 `{out.name}_fixed/` 로 (images/ labels/)
4. 검사: `python scripts/seg_labeling.py check training/datasets/seg_review/{out.name}_fixed`
5. 재학습: `python scripts/retrain_yolo.py --skip-collect --extra training/datasets/seg_review/{out.name}_fixed`

```xml
<View>
  <Image name="image" value="$image"/>
  <PolygonLabels name="label" toName="image">
{label_config}
  </PolygonLabels>
</View>
```

Label Studio 를 쓰지 않으면 `labels/` 의 초벌 YOLO-seg 를 다른 도구(CVAT 등)로 열어 고쳐도 된다.
회원 사진이므로 외부 라벨링 서비스에 올리지 않는다.
""", encoding="utf-8")
    print(f"{len(cases)}장 → {out}")
    return 0


def model_names(model: Path = DEFAULT_MODEL) -> list[str]:
    from ultralytics import YOLO

    return [n for _, n in sorted(YOLO(str(model)).names.items())]


def remap_table(folder_names: list[str], names: list[str]) -> dict[int, int] | None:
    """라벨링 도구가 쓴 클래스 순서(classes.txt) → 모델 순서. 같으면 None, 모델에 없는 이름이 있으면 ValueError."""
    if folder_names == names[: len(folder_names)]:
        return None
    unknown = [n for n in folder_names if n not in names]
    if unknown:
        raise ValueError(f"모델에 없는 클래스 이름: {unknown}")
    return {i: names.index(n) for i, n in enumerate(folder_names)}


def check(args) -> int:
    root: Path = args.folder
    names_n = args.classes
    classes_txt = root / "classes.txt"
    if classes_txt.is_file():
        folder_names = [l.strip() for l in classes_txt.read_text(encoding="utf-8").splitlines() if l.strip()]
        names = model_names(args.model)
        try:
            table = remap_table(folder_names, names)
        except ValueError as e:
            print(f"  ✗ {e}")
            return 1
        if table is not None:
            if not args.fix:
                print("  ✗ classes.txt 순서가 모델 클래스 순서와 다르다 — --fix 로 라벨 번호를 모델 순서로 바꾼다")
                return 1
            for lbl in (root / "labels").glob("*.txt"):
                lines = []
                for line in lbl.read_text(encoding="utf-8").splitlines():
                    parts = line.split()
                    if parts:
                        parts[0] = str(table[int(parts[0])])
                        lines.append(" ".join(parts))
                lbl.write_text("\n".join(lines) + "\n", encoding="utf-8")
            classes_txt.write_text("".join(f"{n}\n" for n in names), encoding="utf-8")
            print(f"  ✓ 라벨 번호를 모델 순서로 바꿈 ({len(table)}개 클래스)")
    images = {p.stem: p for p in (root / "images").glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}}
    labels = {p.stem: p for p in (root / "labels").glob("*.txt")}
    problems: list[str] = []
    for stem in sorted(set(images) - set(labels)):
        problems.append(f"라벨 없음: {stem}")
    for stem in sorted(set(labels) - set(images)):
        problems.append(f"사진 없음: {stem}")
    polys = 0
    for stem, path in sorted(labels.items()):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            parts = line.split()
            try:
                cls = int(parts[0])
                coords = [float(v) for v in parts[1:]]
            except ValueError:
                problems.append(f"{stem}:{n} 숫자가 아님")
                continue
            if not 0 <= cls < names_n:
                problems.append(f"{stem}:{n} 클래스 번호 {cls} (0~{names_n - 1} 이어야)")
            if len(coords) < 6 or len(coords) % 2:
                problems.append(f"{stem}:{n} 폴리곤 점이 3개 미만이거나 좌표 수가 홀수 ({len(coords)})")
            if any(v < 0 or v > 1 for v in coords):
                problems.append(f"{stem}:{n} 좌표가 0~1 밖 (정규화 안 됨?)")
            polys += 1
    print(f"사진 {len(images)} · 라벨 {len(labels)} · 폴리곤 {polys}")
    for p in problems[:50]:
        print("  ✗", p)
    if problems:
        print(f"문제 {len(problems)}건 — 고친 뒤 다시 검사하세요")
        return 1
    print("문제 없음 — 재학습: python scripts/retrain_yolo.py --skip-collect --extra", root)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="세그 실패 사진 라벨링 묶음 만들기 · 검사")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--feedback-dir", type=Path, default=ROOT / "data" / "feedback")
    e.add_argument("--out", type=Path, required=True)
    e.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    e.add_argument("--conf", type=float, default=0.25)
    e.add_argument("--imgsz", type=int, default=1024)
    e.add_argument("--device", default=None)
    e.add_argument("--include-likes", action="store_true", help="좋아요 받은 사례도 (정답에 가까운 예 — 균형용)")
    c = sub.add_parser("check")
    c.add_argument("folder", type=Path)
    c.add_argument("--classes", type=int, default=80)
    c.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="클래스 순서 기준 모델")
    c.add_argument("--fix", action="store_true", help="classes.txt 순서가 다르면 라벨 번호를 모델 순서로 바꾼다")
    args = ap.parse_args()
    return export(args) if args.cmd == "export" else check(args)


if __name__ == "__main__":
    sys.exit(main())
