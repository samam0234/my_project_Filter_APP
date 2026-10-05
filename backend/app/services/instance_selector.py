"""같은 클래스 인스턴스 중 **어느 것**인지 고르기 (위치 · 개수 · 색 속성).

YOLO 는 "사람이 7명"까지만 알려 준다. "맨 앞 빨간 안전모 남자"처럼 특정 인스턴스를
가리키는 요청은 여기서 규칙으로 고른다. 학습이 아니라 인스턴스 간 비교 문제이기 때문.

순서:
  1) attributes (색) — 인스턴스 영역의 HSV 색 비율로 점수화, 기준 이상만 후보
  2) position       — 후보를 위치 기준으로 정렬
  3) rank · count   — rank 번째부터 N 개 (position 만 있으면 1, 아무것도 없으면 전부)

Phase 2 에서 Grounding DINO 가 들어오면 attributes 매칭을 텍스트 그라운딩으로 교체한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from app.schemas.request import InstanceSelector
from app.services.segmentation import Instance

# 【수동·튜닝】 OpenCV HSV (H 0~179, S/V 0~255) 색 범위
# 조명·카메라에 따라 S/V 하한을 조정. 긴 이름("neon yellow")을 먼저 매칭한다.
COLOR_RANGES: Dict[str, List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]] = {
    "neon yellow": [((25, 110, 150), (45, 255, 255))],  # 형광 연두·노랑 (안전 조끼)
    "neon green": [((35, 110, 150), (80, 255, 255))],
    # 빨강은 얼굴 피부(H 0~15, S 60~140)와 겹치므로 채도 하한을 높게
    "red": [((0, 140, 70), (8, 255, 255)), ((170, 140, 70), (179, 255, 255))],
    "orange": [((10, 110, 100), (22, 255, 255))],
    "yellow": [((20, 90, 100), (35, 255, 255))],
    "green": [((35, 70, 50), (85, 255, 255))],
    "blue": [((90, 80, 50), (130, 255, 255))],
    "purple": [((130, 60, 50), (160, 255, 255))],
    "pink": [((150, 40, 130), (175, 200, 255))],
    "brown": [((8, 80, 40), (20, 255, 160))],
    "white": [((0, 0, 190), (179, 40, 255))],
    "gray": [((0, 0, 60), (179, 40, 190))],
    "black": [((0, 0, 0), (179, 255, 55))],
}
COLOR_ALIASES = {
    "neon": "neon yellow",
    "fluorescent": "neon yellow",
    "fluorescent yellow": "neon yellow",
    "grey": "gray",
    "dark": "black",
}

# 【수동·튜닝】 부위 → 인스턴스 bbox 세로 구간 (위=0, 아래=1). person 기준 대략값.
PART_REGIONS: Dict[str, Tuple[float, float]] = {
    "helmet": (0.0, 0.22),
    "hat": (0.0, 0.22),
    "cap": (0.0, 0.22),
    "hair": (0.0, 0.25),
    "vest": (0.18, 0.62),
    "shirt": (0.18, 0.6),
    "jacket": (0.15, 0.65),
    "coat": (0.15, 0.75),
    "top": (0.18, 0.6),
    "hoodie": (0.1, 0.65),
    "sweater": (0.18, 0.62),
    "raincoat": (0.1, 0.8),
    "dress": (0.18, 0.9),
    "skirt": (0.45, 0.8),
    "pants": (0.5, 0.92),
    "jeans": (0.5, 0.92),
    "shoes": (0.85, 1.0),
}

# 같은 영역을 보는 부위 이름은 하나로 (비교·로그 일관성)
PART_ALIASES = {"t-shirt": "shirt", "tee": "shirt", "blouse": "shirt", "sweatshirt": "sweater",
                "trousers": "pants", "sneakers": "shoes", "cap": "hat"}

# 【수동·튜닝】 속성 일치 기준: 절대 비율 이상 **그리고** 최고 점수 대비 상대 비율 이상
# 상대 기준은 여러 인스턴스가 약하게 걸릴 때(피부·배경 색) 확실한 것만 남기기 위함
ATTRIBUTE_MIN_RATIO = 0.06
ATTRIBUTE_RELATIVE_MIN = 0.5
# 【수동·튜닝】 front 점수 = 아래쪽 끝(카메라에 가까움) 가중 + 면적 가중
# 【수동·튜닝】 위치로 고를 때 "눈에 띄는" 인스턴스만 후보로 — 멀리 찍힌 점 같은 사람이 "맨 왼쪽"이 되지 않게.
# 가장 큰 후보 대비 SALIENT_MIN_RATIO 미만이고 이미지 대비 SALIENT_MAX_IMAGE_RATIO 미만이면 제외.
# 실험(scripts/experiments/selection_e2e.py, 600장): 명확한 문항 64.0% → 71.6% (0.05~0.3 비교 중 최고)
SALIENT_MIN_RATIO = 0.2
SALIENT_MAX_IMAGE_RATIO = 0.01
FRONT_WEIGHT_BOTTOM = 0.6
FRONT_WEIGHT_AREA = 0.4


@dataclass
class SelectionResult:
    """선택 결과 + 설명 (로그·피드백 meta 용)."""

    chosen: List[Instance]
    attribute_scores: List[Optional[float]] = field(default_factory=list)
    attribute_matched: Optional[bool] = None  # 속성 조건이 있었을 때 기준 통과 인스턴스 존재 여부
    note: str = ""


def parse_attribute(phrase: str) -> Tuple[Optional[str], Optional[str]]:
    """"red helmet" → ("red", "helmet"). 색이 없으면 (None, part)."""
    text = " ".join(phrase.lower().split())
    padded = f" {text} "
    # 별칭은 긴 것부터 치환 ("fluorescent yellow" 가 "fluorescent" 보다 먼저)
    for alias in sorted(COLOR_ALIASES, key=len, reverse=True):
        if f" {alias} " in padded:
            padded = padded.replace(f" {alias} ", f" {COLOR_ALIASES[alias]} ", 1)
            break
    text = padded.strip()
    # 색도 긴 이름부터 ("neon yellow" 가 "yellow" 보다 먼저)
    color = next(
        (c for c in sorted(COLOR_RANGES, key=len, reverse=True) if f" {c} " in padded),
        None,
    )
    words = f" {text} "
    for alias in sorted(PART_ALIASES, key=len, reverse=True):
        if f" {alias} " in words:
            words = words.replace(f" {alias} ", f" {PART_ALIASES[alias]} ")
    part = next((p for p in PART_REGIONS if f" {p} " in words), None)
    return color, part


def _color_mask(hsv: np.ndarray, color: str) -> np.ndarray:
    out = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in COLOR_RANGES[color]:
        out = cv2.bitwise_or(out, cv2.inRange(hsv, np.array(lo), np.array(hi)))
    return out


def _region(inst: Instance, part: Optional[str]) -> np.ndarray:
    """부위가 있으면 bbox 세로 구간으로 인스턴스 마스크를 자른다."""
    if part is None:
        return inst.mask
    x0, y0, x1, y1 = inst.bbox
    top, bottom = PART_REGIONS[part]
    height = max(1, y1 - y0 + 1)
    ya = y0 + int(top * height)
    yb = y0 + int(np.ceil(bottom * height))
    region = np.zeros_like(inst.mask)
    region[ya:yb, :] = inst.mask[ya:yb, :]
    return region


def attribute_score(inst: Instance, hsv: np.ndarray, attributes: Sequence[str]) -> Optional[float]:
    """인식 가능한 색 속성들의 영역 내 색 비율 평균. 인식 가능한 속성이 없으면 None."""
    ratios: List[float] = []
    for phrase in attributes:
        color, part = parse_attribute(phrase)
        if color is None:
            continue
        region = _region(inst, part)
        total = int(np.count_nonzero(region))
        if total == 0:
            ratios.append(0.0)
            continue
        hit = int(np.count_nonzero(cv2.bitwise_and(_color_mask(hsv, color), region)))
        ratios.append(hit / total)
    if not ratios:
        return None
    return float(np.mean(ratios))


def _centroid(inst: Instance) -> Tuple[float, float]:
    m = cv2.moments(inst.mask, binaryImage=True)
    if m["m00"] == 0:
        x0, y0, x1, y1 = inst.bbox
        return (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return m["m10"] / m["m00"], m["m01"] / m["m00"]


def _sort_by_position(items: List[Instance], position: str, shape: Tuple[int, int]) -> List[Instance]:
    h, w = shape
    if position in {"front", "back"}:
        max_area = max((i.area for i in items), default=1) or 1

        def front_score(i: Instance) -> float:
            return FRONT_WEIGHT_BOTTOM * (i.bbox[3] / max(1, h - 1)) + FRONT_WEIGHT_AREA * (
                i.area / max_area
            )

        return sorted(items, key=front_score, reverse=(position == "front"))
    if position == "left":
        return sorted(items, key=lambda i: _centroid(i)[0])
    if position == "right":
        return sorted(items, key=lambda i: _centroid(i)[0], reverse=True)
    if position == "center":
        cx, cy = w / 2.0, h / 2.0
        return sorted(items, key=lambda i: (_centroid(i)[0] - cx) ** 2 + (_centroid(i)[1] - cy) ** 2)
    if position == "largest":
        return sorted(items, key=lambda i: i.area, reverse=True)
    if position == "smallest":
        return sorted(items, key=lambda i: i.area)
    return items


def _salient(items: List[Instance], shape: Tuple[int, int]) -> List[Instance]:
    """가장 큰 후보에 비해 아주 작은(배경 속 점 같은) 인스턴스를 뺀다. 전부 빠지면 원래 목록."""
    if SALIENT_MIN_RATIO <= 0:
        return items
    largest = max(i.area for i in items) or 1
    image_area = shape[0] * shape[1]
    kept = [
        i for i in items
        if i.area >= SALIENT_MIN_RATIO * largest or i.area >= SALIENT_MAX_IMAGE_RATIO * image_area
    ]
    return kept or items


def select_instances(
    instances: List[Instance],
    selector: Optional[InstanceSelector],
    image_bgr: np.ndarray,
) -> SelectionResult:
    """selector 조건으로 인스턴스를 고른다. selector 가 없으면 전부."""
    if not instances or selector is None or selector.is_empty():
        return SelectionResult(chosen=list(instances))

    candidates = list(instances)
    scores: List[Optional[float]] = []
    matched: Optional[bool] = None
    count = selector.count
    notes: List[str] = []

    # 1) 색 속성
    if selector.attributes:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        scored = [(attribute_score(i, hsv, selector.attributes), i) for i in candidates]
        if all(s is None for s, _ in scored):
            notes.append(f"인식 가능한 색 속성 없음: {selector.attributes}")
        else:
            scores = [s for s, _ in scored]
            best = max((s for s in scores if s is not None), default=0.0)
            cutoff = max(ATTRIBUTE_MIN_RATIO, ATTRIBUTE_RELATIVE_MIN * best)
            passing = [(s, i) for s, i in scored if s is not None and s >= cutoff]
            matched = bool(passing)
            if passing:
                candidates = [i for _, i in sorted(passing, key=lambda t: t[0], reverse=True)]
            else:
                # 기준 통과가 없으면 가장 비슷한 1개만 (전부 남기는 것보다 안전)
                candidates = [i for _, i in sorted(scored, key=lambda t: t[0] or 0.0, reverse=True)]
                count = count or 1
                notes.append("속성 기준 미달 — 가장 가까운 인스턴스 선택")

    # 2) 위치 (rank 만 있고 위치가 없으면 왼쪽부터 센다)
    position = selector.position or ("left" if selector.rank else None)
    if position and len(candidates) > 1:
        salient = _salient(candidates, image_bgr.shape[:2])
        if len(salient) < len(candidates):
            notes.append(f"작은 인스턴스 {len(candidates) - len(salient)}개는 위치 비교에서 제외")
            candidates = salient
    if position:
        candidates = _sort_by_position(candidates, position, image_bgr.shape[:2])
        count = count or 1

    # 3) 순서·개수 — 위치·속성 없이 개수만 있으면 크게 보이는(눈에 띄는) 순
    if count and not position and not selector.attributes:
        candidates = _sort_by_position(candidates, "largest", image_bgr.shape[:2])
    start = (selector.rank or 1) - 1
    if start >= len(candidates):
        notes.append(f"rank {selector.rank} 가 후보 수 {len(candidates)} 보다 큼 — 마지막 것 선택")
        start = max(0, len(candidates) - 1)
    chosen = candidates[start : start + count] if count else candidates[start:]
    return SelectionResult(
        chosen=chosen,
        attribute_scores=scores,
        attribute_matched=matched,
        note="; ".join(notes),
    )
