"""선택한 대상 마스크에서 "다른 인스턴스의 몫"을 덜어낸다 — 지정하지 않은 사람·동물·물체가 대상에 붙어 안 지워지는 문제.

세그 모델의 인스턴스 마스크는 서로 배타적이지 않다. 맞닿거나 겹친 두 사람, 사람과 들고 있는 물건의 마스크는
같은 픽셀을 함께 차지하고, 경계 정제(GrabCut)는 색이 비슷한 이웃 조각을 대상으로 끌어온다.
→ 선택 직후 마스크에서 다른 인스턴스가 차지한 픽셀을 소유권 규칙으로 덜어내고,
   그 자리(금지 구역)는 GrabCut 이 다시 가져가지 못하게 한다.

소유권 규칙 (MASK_EXCLUSIVE)
  off      덜어내지 않는다 (예전 동작)
  subtract 다른 인스턴스가 차지한 픽셀은 모두 덜어낸다
  conf     겹친 픽셀은 신뢰도가 더 높은 쪽이 갖는다 (같거나 대상이 높으면 대상 몫)
  front    겹친 픽셀은 카메라에 더 가까운 쪽(바운딩 박스 아래쪽이 더 낮은 쪽)이 갖는다 — 가린 사람이 앞사람 몫을 못 가져가게
대상 몫이 너무 줄어드는 사고(대상의 절반 이상을 지움)는 막는다: 덜어낸 뒤 면적이 MIN_KEEP 미만이면 덜어내기를 취소.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from app.services.segmentation import Instance

MIN_KEEP = 0.5  # 덜어낸 뒤 남은 면적이 원래의 이 비율 미만이면 취소 (대상을 통째로 잃는 사고 방지)
CORE_ERODE_RATIO = 0.012  # 금지 구역에서 제외할 대상 "안쪽 핵심부" 침식 두께 (긴 변 대비)
FORBID_DILATE_RATIO = 0.004  # 금지 구역을 이웃 경계 바깥으로 넓히는 두께 (긴 변 대비)


def _owns(target: Sequence[Instance], other: Instance, mode: str) -> bool:
    """겹친 픽셀을 other 가 가져가야 하나."""
    if mode == "subtract":
        return True
    t_conf = max((i.confidence for i in target), default=0.0)
    if mode == "conf":
        return other.confidence > t_conf
    if mode == "front":
        t_bottom = max((i.bbox[3] for i in target), default=0)
        return other.bbox[3] > t_bottom or (other.bbox[3] == t_bottom and other.confidence > t_conf)
    return False


def exclusive_mask(
    chosen: Sequence[Instance],
    rest: Sequence[Instance],
    shape: Tuple[int, int],
    mode: str = "subtract",
    min_conf: float = 0.0,
) -> np.ndarray:
    """chosen 의 합집합에서 rest(다른 인스턴스) 중 소유권이 rest 쪽인 픽셀을 덜어낸 마스크 (0/255)."""
    union = np.zeros(shape, np.uint8)
    for inst in chosen:
        union = cv2.bitwise_or(union, inst.mask)
    if mode == "off" or not union.any():
        return union
    taken = np.zeros(shape, np.uint8)
    for other in rest:
        if other.confidence < min_conf or not _owns(chosen, other, mode):
            continue
        taken = cv2.bitwise_or(taken, other.mask)
    result = cv2.bitwise_and(union, cv2.bitwise_not(taken))
    if np.count_nonzero(result) < MIN_KEEP * np.count_nonzero(union):
        return union  # 대상 대부분을 잃게 되면 덜어내지 않는다
    # 덜어낸 뒤 자잘한 조각(대상에서 떨어져 나온 섬)은 가장 큰 덩어리들만 남기고 정리
    return _drop_islands(result, union)


def _drop_islands(result: np.ndarray, original: np.ndarray, keep_ratio: float = 0.04) -> np.ndarray:
    """덜어내고 남은 작은 섬(원래 마스크 면적의 keep_ratio 미만)을 지운다."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats((result > 0).astype(np.uint8), connectivity=8)
    if n <= 2:
        return result
    total = max(int(np.count_nonzero(original)), 1)
    keep = np.zeros_like(result)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= keep_ratio * total:
            keep[labels == i] = 255
    return keep if keep.any() else result


def forbid_zone(
    chosen_mask: np.ndarray,
    rest: Sequence[Instance],
    min_conf: float = 0.0,
) -> Optional[np.ndarray]:
    """GrabCut 이 대상으로 끌어오면 안 되는 구역 = 다른 인스턴스(약간 넓힘) − 대상의 안쪽 핵심부. 없으면 None."""
    if not rest or not chosen_mask.any():
        return None
    h, w = chosen_mask.shape[:2]
    zone = np.zeros((h, w), np.uint8)
    for other in rest:
        if other.confidence >= min_conf:
            zone = cv2.bitwise_or(zone, other.mask)
    if not zone.any():
        return None
    long_side = max(h, w)
    k = max(3, int(long_side * FORBID_DILATE_RATIO) // 2 * 2 + 1)
    zone = cv2.dilate(zone, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    c = max(3, int(long_side * CORE_ERODE_RATIO) // 2 * 2 + 1)
    core = cv2.erode(chosen_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (c, c)))
    zone = cv2.bitwise_and(zone, cv2.bitwise_not(core))
    return zone if zone.any() else None


def rest_instances(all_instances: Sequence[Instance], chosen: Sequence[Instance], others: Sequence[Instance]) -> List[Instance]:
    """대상이 아닌 모든 인스턴스 = 같은 클래스의 선택되지 않은 것 + 다른 클래스 것."""
    chosen_ids = {id(i) for i in chosen}
    return [i for i in all_instances if id(i) not in chosen_ids] + list(others)


def finalize_selection(seg, chosen: Sequence[Instance], shape: Tuple[int, int], settings):
    """선택한 인스턴스 → (대상 마스크, 금지 구역 | None). 사진 노드와 영상이 같이 쓴다.

    선택하지 않은 같은 클래스 인스턴스와 요청하지 않은 다른 클래스 인스턴스(seg.others)가 "rest" 다.
    """
    mask = np.zeros(shape, np.uint8)
    for inst in chosen:
        mask = cv2.bitwise_or(mask, inst.mask)
    if not chosen:
        return mask, None
    rest = rest_instances(seg.instances, chosen, getattr(seg, "others", []))
    if settings.mask_exclusive != "off":
        mask = exclusive_mask(chosen, rest, shape, settings.mask_exclusive, settings.mask_other_min_conf)
    forbid = forbid_zone(mask, rest, settings.mask_other_min_conf) if settings.mask_forbid_refine else None
    return mask, forbid


def leak_signals(seg, chosen: Sequence[Instance], before: np.ndarray, after: np.ndarray) -> dict:
    """정답 없이 서빙 중에도 알 수 있는 "대상에 다른 것이 섞였을 위험" 신호들 (실험으로 상관을 확인한 것만 쓴다).

    removed   : 겹침 덜어내기로 잃은 면적 비율 — 클수록 이웃·물체와 많이 겹쳤다
    touching  : 대상에 맞닿은(경계 1.5% 안) 다른 인스턴스 수 — 붐비는 장면
    crowd     : 맞닿은 다른 인스턴스들이 대상 주변에서 차지하는 면적 / 대상 면적
    big_ratio : 대상 인스턴스 면적 / 같은 클래스 인스턴스 면적의 중앙값 — 두 사람이 한 덩어리가 됐다면 크게 나온다
    conf_min  : 고른 인스턴스의 최소 신뢰도
    """
    area = int(np.count_nonzero(before))
    if not chosen or area == 0:
        return {"removed": 0.0, "touching": 0, "crowd": 0.0, "big_ratio": 1.0, "conf_min": 1.0}
    rest = rest_instances(seg.instances, chosen, getattr(seg, "others", []))
    h, w = before.shape[:2]
    k = max(3, int(max(h, w) * 0.015) // 2 * 2 + 1)
    ring = cv2.dilate(before, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    touching, crowd = 0, 0
    for other in rest:
        hit = cv2.bitwise_and(ring, other.mask)
        if np.count_nonzero(hit) > 0.002 * h * w:
            touching += 1
            crowd += int(np.count_nonzero(hit))
    same = [i.area for i in seg.instances]
    big_ratio = max(i.area for i in chosen) / max(float(np.median(same)), 1.0) if len(same) >= 3 else 1.0
    return {
        "removed": round(1.0 - np.count_nonzero(after) / area, 4),
        "touching": touching,
        "crowd": round(crowd / area, 4),
        "big_ratio": round(float(big_ratio), 3),
        "conf_min": round(min(i.confidence for i in chosen), 3),
    }
