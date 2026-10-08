#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: "남기라고 지정한 대상에 다른 물체·인물·동물이 섞여 안 지워지는" 문제를 정답 주석으로 직접 잰다.

증상: 문장이 한 대상만 가리켜도(해석은 정확) 결과 마스크에 지정하지 않은 사람·동물·물체 조각이 붙어 남는다.
방법: COCO val2017 **인스턴스 정답 폴리곤**으로 각 사진에서
  target = 사용자가 지정한 인스턴스(들),  others = 그 밖의 모든 정답 인스턴스(다른 사람·개·가방·의자…, target 과 겹친 부분은 target 몫)
를 만든 뒤, 서빙과 같은 경로(전처리 → 세그 → 인스턴스 선택 → 원본 크기 → 경계 정제 → 효과)를 돌려 단계별 마스크를 잡는다.

단계별로 잡는 마스크 (어디서 새는지 가르려고):
  select : 인스턴스 선택 직후(전처리 해상도) — 세그 모델 + 선택기의 책임
  refine : 원본 크기로 키운 뒤 GrabCut 정제 직전 (선택 마스크를 확대한 것)
  final  : 효과 함수가 받는 최종 마스크 — GrabCut 정제 후

지표 (마스크 M, 정답 target T, 정답 others O):
  leak       = |M ∩ O| / |M|             섞인 비율 — 핵심. 낮을수록 좋다
  iou        = |M ∩ T| / |M ∪ T|
  cover      = |M ∩ T| / |T|             대상을 얼마나 덮었나 (잃으면 안 된다)
  leak_case  = leak > 5% 인 사진의 비율   "눈에 띄게 섞인" 사진 비율
  pick_ok    = 고른 인스턴스가 정답 대상과 IoU 0.5 이상인 비율 (선택 단계 정확도)

실행: python scripts/experiments/leak_eval.py --list
      python scripts/experiments/leak_eval.py --rounds all --n 48 --out docs/vaildates/leak_eval_20261008.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
ANN = ROOT / "training/datasets/coco_raw/annotations/instances_val2017.json"
IMAGE_DIRS = [ROOT / "training/datasets/coco_val_sel/images/val", ROOT / "training/datasets/coco_leak/images"]
BIG = 0.025  # "눈에 띄는" 인스턴스 = 화면의 2.5% 이상
TINY = 0.003  # 이보다 작은 건 사람이 봐도 구분이 모호해 "깨끗한" 사례에서는 후보로 세지 않는다


# --------------------------------------------------------------------------- 정답


@dataclass
class GT:
    path: Path
    shape: tuple
    instances: List[dict] = field(default_factory=list)  # {cat, mask(bool), area, cx, cy}


def download_extra(classes=("dog", "cat", "horse", "sheep", "cow", "elephant", "bear"), per_class: int = 70) -> int:
    """동물 사진이 모자라 COCO val2017 에서 (동물 + 사람이 함께 있는) 사진을 더 받는다. git 무시 폴더."""
    import urllib.request

    data = json.loads(ANN.read_text(encoding="utf-8"))
    cats = {c["name"]: c["id"] for c in data["categories"]}
    by_image: Dict[int, list] = {}
    for a in data["annotations"]:
        by_image.setdefault(a["image_id"], []).append(a)
    info = {i["id"]: i for i in data["images"]}
    dest = IMAGE_DIRS[1]
    dest.mkdir(parents=True, exist_ok=True)
    have = {p.stem for d in IMAGE_DIRS for p in d.glob("*.jpg")}
    got = 0
    for cls in classes:
        n = 0
        for iid, anns in sorted(by_image.items()):
            if n >= per_class:
                break
            im = info[iid]
            area = im["width"] * im["height"]
            has = [a for a in anns if a["category_id"] == cats[cls] and not a.get("iscrowd") and a["area"] >= BIG * area]
            persons = [a for a in anns if a["category_id"] == cats["person"] and not a.get("iscrowd") and a["area"] >= BIG * area]
            if not has or not persons or f"{iid:012d}" in have:
                continue
            urllib.request.urlretrieve(im["coco_url"], dest / f"{iid:012d}.jpg")
            have.add(f"{iid:012d}")
            n += 1
            got += 1
    return got


def load_gt(limit: Optional[int] = None) -> List[GT]:
    data = json.loads(ANN.read_text(encoding="utf-8"))
    cats = {c["id"]: c["name"] for c in data["categories"]}
    by_image: Dict[int, list] = {}
    for a in data["annotations"]:
        if a.get("iscrowd") or not isinstance(a["segmentation"], list):
            continue
        by_image.setdefault(a["image_id"], []).append(a)
    out: List[GT] = []
    paths = sorted(p for d in IMAGE_DIRS for p in d.glob("*.jpg"))
    for path in paths:
        anns = by_image.get(int(path.stem))
        if not anns:
            continue
        img = cv2.imread(str(path))
        if img is None:
            continue
        h, w = img.shape[:2]
        gt = GT(path=path, shape=(h, w))
        for a in anns:
            m = np.zeros((h, w), np.uint8)
            for poly in a["segmentation"]:
                if len(poly) >= 6:
                    cv2.fillPoly(m, [np.array(poly, np.float32).reshape(-1, 2).round().astype(np.int32)], 1)
            area = int(m.sum())
            if area == 0:
                continue
            ys, xs = np.nonzero(m)
            gt.instances.append({"cat": cats[a["category_id"]], "mask": m.astype(bool), "area": area,
                                 "cx": float(xs.mean()), "cy": float(ys.mean())})
        out.append(gt)
        if limit and len(out) >= limit:
            break
    return out


def big(gt: GT, cat: str) -> List[dict]:
    return [i for i in gt.instances if i["cat"] == cat and i["area"] >= BIG * gt.shape[0] * gt.shape[1]]


# --------------------------------------------------------------------------- 사례 (시나리오)


@dataclass
class Case:
    gt: GT
    prompt: dict  # ParsedPrompt 필드
    target: np.ndarray  # bool — 지정한 인스턴스(들)
    others: np.ndarray  # bool — 그 밖의 정답 인스턴스들 (target 과 겹친 부분 제외)
    expect: List[dict]  # 정답 인스턴스 정보 (선택 정확도용)


def _mk(gt: GT, parsed: dict, targets: List[dict], same_class_ok: bool = False) -> Case:
    """same_class_ok: 클래스 단위 요청("사람만")이면 같은 클래스의 작은 인스턴스도 대상이지 섞임이 아니다."""
    t = np.zeros(gt.shape, bool)
    for i in targets:
        t |= i["mask"]
    classes = {i["cat"] for i in targets}
    o = np.zeros(gt.shape, bool)
    for i in gt.instances:
        if any(i is x for x in targets):
            continue
        if same_class_ok and i["cat"] in classes:
            t |= i["mask"]
            continue
        o |= i["mask"]
    return Case(gt=gt, prompt=parsed, target=t, others=o & ~t, expect=targets)


def clean_persons(gt: GT) -> Optional[List[dict]]:
    """위치로 가리킬 때 모호하지 않은 사진만: 눈에 띄는 사람이 전부 '큰' 사람이고 중간 크기 사람이 없다. 아니면 None."""
    img_area = gt.shape[0] * gt.shape[1]
    visible = [i for i in gt.instances if i["cat"] == "person" and i["area"] >= TINY * img_area]
    if len(visible) < 2 or any(i["area"] < BIG * img_area for i in visible):
        return None
    return sorted(visible, key=lambda i: i["cx"])


def scenario_cases(name: str, pool: List[GT]) -> List[Case]:
    """시나리오 이름 → 사례 목록. 같은 이름이면 항상 같은 사진이 나온다 (변형 비교가 짝지어지도록)."""
    cases: List[Case] = []
    for gt in pool:
        loose = sorted(big(gt, "person"), key=lambda i: i["cx"])  # 큰 사람만 (작은/중간 크기 사람이 있어도 무시 — 모호함 포함)
        persons = clean_persons(gt) or []
        sel = lambda **kw: {"target": ["person"], "effect": "remove_bg", "selector": {"count": 1, **kw}}  # noqa: E731
        if name == "left" and persons:
            cases.append(_mk(gt, sel(position="left"), [persons[0]]))
        elif name == "left_loose" and len(loose) >= 2:
            cases.append(_mk(gt, sel(position="left"), [loose[0]]))
        elif name == "right" and persons:
            cases.append(_mk(gt, sel(position="right"), [persons[-1]]))
        elif name == "largest" and persons:
            cases.append(_mk(gt, sel(position="largest"), [max(persons, key=lambda i: i["area"])]))
        elif name == "rank2" and len(persons) >= 3:
            cases.append(_mk(gt, sel(position="left", rank=2), [persons[1]]))
        elif name == "all_persons":
            persons_all = [i for i in gt.instances if i["cat"] == "person"]
            others = [i for i in gt.instances if i["cat"] != "person" and i["area"] >= 0.01 * gt.shape[0] * gt.shape[1]]
            if big(gt, "person") and others:
                cases.append(_mk(gt, {"target": ["person"], "effect": "remove_bg", "selector": None}, persons_all, True))
        elif name in ("dog", "cat", "horse", "sheep", "cow", "elephant", "bear", "car"):
            same = [i for i in gt.instances if i["cat"] == name]
            if big(gt, name) and big(gt, "person"):
                cases.append(_mk(gt, {"target": [name], "effect": "remove_bg", "selector": None}, same, True))
        elif name == "remove_left" and persons:
            cases.append(_mk(gt, {"target": ["person"], "effect": "remove_object",
                                  "selector": {"position": "left", "count": 1}}, [persons[0]]))
        elif name == "touching" and persons:
            # 서로 겹치거나 맞닿은 두 사람 — 가장 새기 쉬운 경우
            a, b = persons[0], persons[1]
            if (a["mask"] & b["mask"]).any() or (cv2.dilate(a["mask"].astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & b["mask"]).any():
                cases.append(_mk(gt, sel(position="left"), [a]))
        elif name == "one_person_with_objects":
            # 사람 한 명뿐인 사진에서 사람 옆 물체(가방·의자·스케이트보드…)가 섞이나
            only = [i for i in gt.instances if i["cat"] == "person" and i["area"] >= 0.5 * TINY * gt.shape[0] * gt.shape[1]]
            others = [i for i in gt.instances if i["cat"] != "person" and i["area"] >= 0.005 * gt.shape[0] * gt.shape[1]]
            if len(only) == 1 and big(gt, "person") and others:
                cases.append(_mk(gt, {"target": ["person"], "effect": "remove_bg", "selector": None}, only, True))
    return cases


# --------------------------------------------------------------------------- 파이프라인 + 단계별 마스크 수집


class Tap:
    """서빙 코드에 끼워 넣어 단계별 마스크를 수집한다 (동작은 바꾸지 않는다)."""

    def __init__(self) -> None:
        self.select = None  # (mask 전처리 해상도, chosen instances)
        self.all_instances = None  # 선택 전 대상 클래스 인스턴스 전부
        self.refine_in = None
        self.final = None


def _json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(f"{type(o)} 직렬화 불가")


def _boundary_f(pred: np.ndarray, gt: np.ndarray) -> float:
    """DAVIS 식 경계 F (허용 오차 = 대각선의 0.4%, 최소 2px)."""
    h, w = gt.shape[:2]
    tol = max(2, int(round(0.004 * (h * h + w * w) ** 0.5)))
    k3 = np.ones((3, 3), np.uint8)
    kt = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))

    def edge(m):
        b = m.astype(np.uint8)
        return b - cv2.erode(b, k3)

    bp, bg = edge(pred), edge(gt)
    if bp.sum() == 0 or bg.sum() == 0:
        return 0.0
    precision = (bp & cv2.dilate(bg, kt)).sum() / bp.sum()
    recall = (bg & cv2.dilate(bp, kt)).sum() / bg.sum()
    return float(2 * precision * recall / max(precision + recall, 1e-9))


def _resize_bool(mask: np.ndarray, shape: tuple) -> np.ndarray:
    if mask.shape[:2] != tuple(shape):
        mask = cv2.resize(mask.astype(np.uint8), (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    return mask > 127 if mask.dtype == np.uint8 and mask.max() > 1 else mask > 0


@contextlib.contextmanager
def tapped(tap: Tap, patches: Optional[Callable] = None):
    from app.services import effects
    from app.workflows import nodes

    orig_select, orig_refine, orig_apply = nodes.select_instances, effects.refine_mask, effects.apply_effects

    def select(instances, selector, image):
        out = orig_select(instances, selector, image)
        tap.select = (list(out.chosen), image.shape[:2])
        tap.all_instances = list(instances)
        return out

    def refine(mask, image=None, forbid=None):
        tap.refine_in = mask.copy()
        return orig_refine(mask, image, forbid)

    def apply(image, mask, parsed, **kw):
        tap.final = mask.copy()
        return orig_apply(image, mask, parsed, **kw)

    nodes.select_instances, effects.refine_mask, effects.apply_effects = select, refine, apply
    # effect_applier 는 호출 때마다 effects 에서 import 하므로 위 교체가 적용된다
    cm = patches() if patches else contextlib.nullcontext()
    try:
        with cm:
            yield
    finally:
        nodes.select_instances, effects.refine_mask, effects.apply_effects = orig_select, orig_refine, orig_apply


def run_case(case: Case, tmp: Path, patches: Optional[Callable] = None) -> dict:
    from app.core.config import get_settings
    from app.schemas.request import ParsedPrompt
    from app.workflows.graph import run_pipeline

    get_settings().upload_dir = str(tmp)
    img = cv2.imread(str(case.gt.path))
    ok, buf = cv2.imencode(".jpg", img)
    tap = Tap()
    parsed = ParsedPrompt(**case.prompt)
    t0 = time.perf_counter()
    with tapped(tap, patches):
        res = run_pipeline(buf.tobytes(), "leak-eval", persist=False, parsed=parsed)
    dt = time.perf_counter() - t0
    shutil.rmtree(tmp / res.job_id, ignore_errors=True)
    h, w = case.gt.shape
    out: dict = {"image": case.gt.path.stem, "seconds": dt, "status": res.status, "signals": (res.meta or {}).get("leak")}

    def metrics(mask: Optional[np.ndarray]) -> Optional[dict]:
        if mask is None or not mask.any():
            return {"leak": 0.0, "iou": 0.0, "cover": 0.0, "empty": True}
        m = _resize_bool(mask, (h, w))
        inter = (m & case.target).sum()
        return {
            "leak": float((m & case.others).sum() / max(m.sum(), 1)),
            "iou": float(inter / max((m | case.target).sum(), 1)),
            "cover": float(inter / max(case.target.sum(), 1)),
            "bf": _boundary_f(m, case.target),
            "empty": False,
        }

    sel_mask = None
    pick_ok = None
    if tap.select is not None:
        chosen, sel_shape = tap.select
        sel_mask = np.zeros(sel_shape, np.uint8)
        for inst in chosen:
            sel_mask |= (inst.mask > 0).astype(np.uint8) * 255
        # 선택 정확도: 고른 인스턴스 각각이 정답 대상 중 하나와 IoU 0.5 이상인가
        ok_all = bool(chosen)
        for inst in chosen:
            m = _resize_bool(inst.mask, (h, w))
            best = max(((m & e["mask"]).sum() / max((m | e["mask"]).sum(), 1)) for e in case.expect)
            ok_all &= best >= 0.5
        pick_ok = ok_all and len(chosen) == len(case.expect) if case.prompt.get("selector") else ok_all
    # 인스턴스 단위 진단 (정답 대상 클래스의 눈에 띄는 인스턴스 기준): 검출 누락 · 두 사람이 한 덩어리로 합쳐짐
    if tap.all_instances is not None:
        cls = case.prompt["target"][0]
        gts = [i for i in case.gt.instances if i["cat"] == cls and i["area"] >= BIG * h * w]
        preds = [_resize_bool(i.mask, (h, w)) for i in tap.all_instances]
        found = merged = 0
        for g in gts:
            if any(((p & g["mask"]).sum() / max((p | g["mask"]).sum(), 1)) >= 0.5 for p in preds):
                found += 1
        for p in preds:
            covered = sum(1 for g in gts if (p & g["mask"]).sum() / max(g["area"], 1) >= 0.3)
            merged += covered >= 2
        out["gt_n"], out["found"], out["pred_n"], out["merged"] = len(gts), found, len(preds), int(merged)
    out["select"] = metrics(sel_mask)
    out["refine"] = metrics(tap.refine_in)
    out["final"] = metrics(tap.final)
    out["pick_ok"] = pick_ok
    return out


# --------------------------------------------------------------------------- 라운드 (실험 변형)


@contextlib.contextmanager
def _patch(module, **attrs):
    old = {k: getattr(module, k) for k in attrs}
    for k, v in attrs.items():
        setattr(module, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


@dataclass
class Round:
    name: str
    scenario: str
    desc: str
    patches: Optional[Callable] = None


def build_rounds() -> List[Round]:
    from app.core.config import get_settings
    from app.services import effects
    from app.services.image_processor import ImageProcessor

    cfg = get_settings()

    def no_grabcut():
        orig = effects.refine_mask

        def morph_only(mask, image=None, forbid=None):
            return orig(mask, None, None)

        return _patch(effects, refine_mask=morph_only)

    def settings(**kw):
        return lambda: _patch(cfg, **kw)

    def no_clahe():
        import cv2 as _cv2

        from app.utils.image_utils import resize_keep_aspect

        def plain(self, image):
            return resize_keep_aspect(image.copy(), self.settings.max_image_side)[0]

        return _patch(ImageProcessor, preprocess=plain)

    R = Round
    return [
        # --- A: 진단 — 현재 코드에서 시나리오별로 얼마나·어디서 새는지
        R("A01", "left", "기준선: 가장 왼쪽 사람 한 명 (깨끗한 사진)"),
        R("A02", "right", "기준선: 가장 오른쪽 사람 한 명"),
        R("A03", "largest", "기준선: 가장 큰 사람 한 명"),
        R("A04", "rank2", "기준선: 왼쪽에서 두 번째 사람"),
        R("A05", "all_persons", "기준선: 사람 전부 (다른 물체가 섞이나)"),
        R("A06", "touching", "기준선: 서로 맞닿은 두 사람 중 왼쪽"),
        R("A07", "dog", "기준선: 강아지만 (사람이 섞이나)"),
        R("A08", "cat", "기준선: 고양이만"),
        R("A09", "car", "기준선: 자동차만 (사람이 섞이나)"),
        R("A10", "remove_left", "기준선: 왼쪽 사람 지우기 (지울 마스크에 남이 섞이나)"),
        R("A11", "left_loose", "기준선: 왼쪽 사람 — 모호한 사진 포함 (정의 차이 확인)"),
        R("A12", "one_person_with_objects", "기준선: 사람 한 명 + 주변 물체 (사람 옆 물체가 섞이나)"),
        R("A13", "horse", "기준선: 말만"),
        R("A14", "sheep", "기준선: 양만"),
        R("A15", "elephant", "기준선: 코끼리만"),
        # --- B: 가설별 변형 (같은 사진으로 A 와 짝지어 비교)
        # H1 경계 정제(GrabCut)가 이웃 조각을 끌어온다
        R("B01", "left", "H1 GrabCut 끔", no_grabcut),
        R("B02", "touching", "H1 맞닿은 사람 + GrabCut 끔", no_grabcut),
        R("B03", "rank2", "H1 둘째 사람 + GrabCut 끔", no_grabcut),
        R("B04", "all_persons", "H1 사람 전부 + GrabCut 끔", no_grabcut),
        # H4 인스턴스 마스크가 서로 겹친다 → 다른 인스턴스 몫을 덜어낸다
        R("B05", "left", "H4 겹침 덜어내기: 전부(subtract)", settings(mask_exclusive="subtract")),
        R("B06", "touching", "H4 맞닿은 사람 + subtract", settings(mask_exclusive="subtract")),
        R("B07", "touching", "H4 맞닿은 사람 + 신뢰도 높은 쪽 소유(conf)", settings(mask_exclusive="conf")),
        R("B08", "touching", "H4 맞닿은 사람 + 앞사람 소유(front)", settings(mask_exclusive="front")),
        # H5 정제가 이웃 구역으로 번지지 못하게 금지 구역
        R("B09", "touching", "H5 맞닿은 사람 + 금지 구역만", settings(mask_forbid_refine=True)),
        R("B10", "rank2", "H5 둘째 사람 + 금지 구역만", settings(mask_forbid_refine=True)),
        R("B11", "left", "H4+H5 subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        R("B12", "touching", "H4+H5 맞닿은 사람 + subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        R("B13", "rank2", "H4+H5 둘째 사람 + subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        # H6 다른 클래스(물체·사람)가 대상에 섞인다
        R("B14", "all_persons", "H6 사람 전부 + subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        R("B15", "one_person_with_objects", "H6 사람 한 명+물체 + subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        R("B16", "car", "H6 자동차 + subtract + 금지 구역 (사람이 안 섞이나)", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        R("B17", "cat", "H6 고양이 + subtract + 금지 구역", settings(mask_exclusive="subtract", mask_forbid_refine=True)),
        # H2/H3 세그 모델 자체 — 입력 크기 · NMS · 신뢰도 · 전처리
        R("B18", "left", "H2 입력 크기 960", settings(seg_imgsz=960)),
        R("B19", "touching", "H2 맞닿은 사람 + 입력 크기 1280", settings(seg_imgsz=1280)),
        R("B20", "touching", "H2 맞닿은 사람 + NMS iou 0.5", settings(seg_nms_iou=0.5)),
        R("B21", "touching", "H3 맞닿은 사람 + 신뢰도 0.15", settings(min_confidence=0.15)),
        R("B22", "left", "H3 신뢰도 0.4", settings(min_confidence=0.4)),
        R("B23", "left", "H7 CLAHE 전처리 끔", no_clahe),
    ] + recipe_rounds(settings, no_grabcut, no_clahe) + model_rounds(settings, no_grabcut, no_clahe) + [
        # F: 새 기본값(CLAHE 끔 · GrabCut 끔 · 겹침 덜어내기)으로 위험 신호(meta.leak)를 기록 — 신호가 실제 섞임·오선택과 상관 있나
        R(f"F-{scen}", scen, "새 기본값 + 위험 신호 기록")
        for scen in ("left", "right", "largest", "rank2", "touching", "all_persons", "one_person_with_objects", "car", "dog")
    ]


RECIPES = {
    # 이름: (설명, 설정 변경, GrabCut 끔?, CLAHE 끔?)
    "R0": ("현재(기준)", {}, False, False),
    "R1": ("CLAHE 끔", {}, False, True),
    "R2": ("CLAHE 끔 + GrabCut 끔", {}, True, True),
    "R3": ("CLAHE 끔 + GrabCut 끔 + 겹침 덜어내기", {"mask_exclusive": "subtract"}, True, True),
    "R4": ("CLAHE 끔 + 덜어내기 + 금지 구역(GrabCut 유지)", {"mask_exclusive": "subtract", "mask_forbid_refine": True}, False, True),
    "R5": ("R3 + 신뢰도 0.15", {"mask_exclusive": "subtract", "min_confidence": 0.15}, True, True),
}
RECIPE_SCENARIOS = ["left", "rank2", "touching", "all_persons", "one_person_with_objects", "car"]


def recipe_rounds(settings, no_grabcut, no_clahe):
    """같은 사진으로 레시피를 짝지어 비교하는 큰 라운드 (D-R<번호>-<시나리오>)."""
    out = []
    for rid, (desc, cfg, drop_gc, drop_clahe) in RECIPES.items():
        for scen in RECIPE_SCENARIOS:
            def patches(cfg=cfg, drop_gc=drop_gc, drop_clahe=drop_clahe):
                @contextlib.contextmanager
                def cm():
                    with contextlib.ExitStack() as st:
                        if cfg:
                            st.enter_context(settings(**cfg)())
                        if drop_gc:
                            st.enter_context(no_grabcut())
                        if drop_clahe:
                            st.enter_context(no_clahe())
                        yield
                return cm()
            out.append(Round(f"D-{rid}-{scen}", scen, f"{rid} {desc}", patches))
    return out


MODEL_FILES = {"s": "yolo26s-seg.pt", "m": "yolo26m-seg.pt", "l": "yolo26l-seg.pt", "x": "yolo26x-seg.pt"}


def model_rounds(settings, no_grabcut, no_clahe):
    """세그 모델 크기 비교 (E-<모델>-<시나리오>) — 후처리는 R3(CLAHE 끔 · GrabCut 끔 · 겹침 덜어내기)로 고정."""
    out = []
    for key, fname in MODEL_FILES.items():
        for scen in ("left", "rank2", "touching"):
            def patches(fname=fname):
                @contextlib.contextmanager
                def cm():
                    from app.core.config import Settings
                    from app.services.image_processor import ImageProcessor
                    from app.services.segmentation import Segmentor
                    from app.workflows import nodes

                    cfg = Settings.model_validate({"DB_DIALECT": "sqlite", "PRELOAD_MODELS": False, "SEG_PREFER_ONNX": False,
                                                   "YOLO_MODEL_PATH": f"models/{fname}", "MASK_EXCLUSIVE": "subtract"})
                    proc = ImageProcessor(cfg, segmentor=Segmentor(cfg))
                    with contextlib.ExitStack() as st:
                        st.enter_context(_patch(nodes, _processor=proc))
                        st.enter_context(no_grabcut())
                        st.enter_context(no_clahe())
                        yield
                return cm()
            out.append(Round(f"E-{key}-{scen}", scen, f"모델 yolo26{key} + R3 후처리", patches))
    return out


# --------------------------------------------------------------------------- 실행


def summarize(rows: List[dict]) -> dict:
    out = {"n": len(rows)}
    for stage in ("select", "refine", "final"):
        vals = [r[stage] for r in rows if r.get(stage) and not r[stage]["empty"]]
        empty = sum(1 for r in rows if r.get(stage) and r[stage]["empty"])
        if not vals:
            out[stage] = {"empty": empty}
            continue
        leak = np.array([v["leak"] for v in vals])
        out[stage] = {
            "leak": round(float(leak.mean()), 4),
            "leak_case5": round(float((leak > 0.05).mean()), 3),
            "leak_case15": round(float((leak > 0.15).mean()), 3),
            "iou": round(float(np.mean([v["iou"] for v in vals])), 4),
            "cover": round(float(np.mean([v["cover"] for v in vals])), 4),
            "bf": round(float(np.mean([v.get("bf", 0.0) for v in vals])), 4),
            "empty": empty,
        }
    picks = [r["pick_ok"] for r in rows if r.get("pick_ok") is not None]
    out["pick_ok"] = round(float(np.mean(picks)), 3) if picks else None
    # 선택이 맞은 사진만 — 엉뚱한 인스턴스를 고른 탓이 아닌 "마스크 자체의 번짐"
    good = [r for r in rows if r.get("pick_ok") in (True, None) and r.get("final") and not r["final"]["empty"]]
    if good:
        for stage in ("select", "final"):
            vals = [r[stage]["leak"] for r in good if r.get(stage) and not r[stage]["empty"]]
            if vals:
                out[f"{stage}_leak_pick_ok"] = round(float(np.mean(vals)), 4)
                out[f"{stage}_leak_case5_pick_ok"] = round(float((np.array(vals) > 0.05).mean()), 3)
        out["n_pick_ok"] = len(good)
    out["seconds"] = round(float(np.mean([r["seconds"] for r in rows])), 3)
    gt_n = sum(r.get("gt_n", 0) for r in rows)
    if gt_n:
        out["det_recall"] = round(sum(r.get("found", 0) for r in rows) / gt_n, 3)  # 눈에 띄는 대상을 검출했나
        out["merged_cases"] = round(sum(1 for r in rows if r.get("merged")) / len(rows), 3)  # 두 인스턴스가 한 덩어리가 된 사진 비율
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", default="all", help="all 또는 A01,B03 처럼 쉼표 목록")
    ap.add_argument("--n", type=int, default=48, help="라운드마다 사진 수 상한")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--download", action="store_true", help="동물 사진을 COCO 에서 더 받는다 (한 번만)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--rows-out", type=Path, default=None, help="사진별 원자료까지 저장 (분석용, 크다)")
    args = ap.parse_args()

    rounds = build_rounds()
    if args.list:
        for r in rounds:
            print(r.name, r.scenario, r.desc)
        return
    if args.download:
        print("추가로 받은 사진", download_extra())
    wanted = None if args.rounds == "all" else set(args.rounds.split(","))
    pool = load_gt()
    print(f"정답 로드: 사진 {len(pool)}장")
    tmp = Path(tempfile.mkdtemp(prefix="leak-eval-"))
    results = {}
    try:
        for rnd in rounds:
            if wanted and rnd.name not in wanted:
                continue
            cases = scenario_cases(rnd.scenario, pool)[: args.n]
            rows = [run_case(c, tmp, rnd.patches) for c in cases]
            results[rnd.name] = {"scenario": rnd.scenario, "desc": rnd.desc, "summary": summarize(rows), "rows": rows}
            s = results[rnd.name]["summary"]
            f = s.get("final", {})
            print(f"{rnd.name} {rnd.scenario:12} n={s['n']:3} 선택정확 {s['pick_ok']} | 전체 leak {f.get('leak')} (5%초과 {f.get('leak_case5')}) "
                  f"iou {f.get('iou')} cover {f.get('cover')} bf {f.get('bf')} | 선택맞은것만 n={s.get('n_pick_ok')} select {s.get('select_leak_pick_ok')} → "
                  f"final {s.get('final_leak_pick_ok')} (5%초과 {s.get('final_leak_case5_pick_ok')}) | 검출재현 {s.get('det_recall')} 합쳐짐 {s.get('merged_cases')} | {rnd.desc}", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if args.rows_out:
        args.rows_out.write_text(json.dumps(results, ensure_ascii=False, default=_json_default), encoding="utf-8")
    if args.out:
        slim = {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in results.items()}
        args.out.write_text(json.dumps(slim, ensure_ascii=False, indent=1, default=_json_default), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
