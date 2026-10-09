"""영상 · GIF 에서 고른 인스턴스를 프레임 사이로 따라가기.

"왼쪽 사람" · "맨 앞 사람" 같은 selector 를 프레임마다 다시 적용하면, 두 사람이 서로 지나가는 순간
"왼쪽"이 다른 사람으로 바뀌어 효과가 그 사람으로 옮겨 간다. 그래서 selector 는 **처음 한 번(또는 놓쳤을 때)** 만 쓰고,
이후 프레임에서는 직전에 고른 인스턴스와 같은 것을 찾는다. 고르지 않은 사람들도 같이 따라가서(다중 추적),
앞을 지나가는 다른 사람은 그 사람의 추적이 먼저 가져가게 한다 — 고른 대상이 가려지는 동안 그 사람으로 옮겨 가지 않게.

같은 것 판정 (축소 마스크로 계산):
  - 위치: 직전 마스크를 속도(무게중심 이동)만큼 옮긴 예측과의 IoU
  - 생김새: 마스크 안 HSV 색 분포(H·S 히스토그램) 유사도 — 겹쳐 지나갈 때 위치만으로는 헷갈리는 걸 가른다
  점수 = IoU × (1 − APPEARANCE_WEIGHT) + 색 유사도 × APPEARANCE_WEIGHT, IoU 가 MIN_IOU 이상이고 색 유사도가 MIN_LOOK 이상인 것만 후보.
  모든 추적에 대해 점수가 높은 짝부터 하나씩 짝짓는다 (한 인스턴스를 두 추적이 가져가지 않게).

일부만 보이면(다른 사람에게 가려지는 중) 보이는 조각의 무게중심이 뒤로 밀려 속도가 틀어지므로, 속도 · 기준 모습은 그대로 두고
예측 위치를 이어 간다. 놓치면(가려짐 · 검출 실패) 예측 위치를 속도만큼 계속 옮기며 MAX_LOST 프레임까지 기다리고 (그동안 빈 결과 →
FrameRenderer 가 직전 마스크 유지), 그 뒤로는 색 분포가 아주 비슷한 사람(REID_LOOK)이 보이면 그 사람으로 이어 가고,
그것도 없으면 이미 따라가는 다른 사람이 아닌 새로 나타난 사람 중 selector 가 고르는 사람으로 이어 간다(다시 들어오는 대상),
RESELECT_LOST 프레임이 지나도록 못 찾으면 selector 로 다시 고른다.

실제 검출기 잡음 대비 (YOLO 로 잰 실패에서):
  - 한 사람이 겹친 마스크 두 개로 검출되면 하나를 "다른 사람"으로 따라가다 대상을 빼앗는다 → 고른 대상과 크게 겹치는 마스크는 중복으로 보고 따로 추적하지 않는다
  - 지나치는 순간 두 사람이 한 마스크로 합쳐지면 기준 색이 오염된다 → 면적이 평소의 1.5배를 넘으면 기준 모습을 갱신하지 않는다

개수가 정해지지 않은 selector(예: "빨간 옷 입은 사람들" — 조건 맞는 전부)는 새로 들어온 사람도 포함해야 하므로 추적하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np

from app.schemas.request import InstanceSelector
from app.services.instance_selector import select_instances
from app.services.segmentation import Instance

TRACK_SIDE = 160  # 비교용 축소 크기 (긴 변)
MIN_IOU = 0.15  # 예측 위치와 이만큼은 겹쳐야 같은 대상 후보
APPEARANCE_WEIGHT = 0.4
MIN_LOOK = 0.35  # 색 분포 유사도가 이 아래면 위치가 겹쳐도 다른 대상 (지나치며 겹친 다른 사람으로 옮겨 가지 않게)
REACQUIRE_PX = 3  # 놓친 대상을 다시 잡을 때 예측 위치를 이만큼(축소 기준 px) 넓혀 본다 (크기 비례로 넓히면 DAVIS drone 이 나빠졌다)
MAX_LOST = 8  # 이 프레임 수보다 오래 못 찾으면 위치 예측을 버리고 색 분포로 다시 찾는다 (다른 사람 추적은 이때 지운다)
RESELECT_LOST = 24  # 이보다 오래 못 찾으면 selector 로 다시 고른다 (초당 30프레임이면 약 0.8초 — 지나치며 가려지는 시간보다 길게)
VELOCITY_DECAY = 0.9  # 놓친 동안 예측 속도를 조금씩 줄인다 (멈춘 대상이 멀리 날아가지 않게)
PARTIAL = 0.7  # 보이는 면적이 평소의 이 비율 미만이면 "일부 가려짐" — 조각의 무게중심은 믿지 않고 예측 위치를 이어 간다
MERGED = 1.5  # 면적이 평소의 이 배를 넘고 다른 추적 대상과 겹치면 옆 사람과 한 덩어리로 검출된 것 — 기준 모습(마스크 · 색)을 갱신하지 않는다
DUPLICATE = 0.6  # 같은 프레임의 두 마스크가 작은 쪽 면적의 이 비율 넘게 겹치면 같은 사람의 중복 검출
NEWCOMER_MIN = 0.15  # 새로 나타난 사람으로 이어 갈 때 평소 대상 면적의 이 비율 이상만 (작은 오검출로 옮겨 가지 않게)
MAX_SPEED = 0.08  # 예측 속도 상한 — 프레임당 축소 화면 긴 변의 이 비율 (잘못 잡았다 바로잡을 때의 점프가 속도로 남지 않게)
REID_LOOK = 0.6  # 오래 놓친 뒤 selector 로 다시 고르기 전에, 색 분포가 이만큼 비슷한 사람이 있으면 그 사람으로 이어 간다


def should_track(selector: Optional[InstanceSelector]) -> bool:
    """정해진 개수를 고르는 selector 일 때만 추적한다 (위치 · 순서 · 개수 중 하나라도 있으면)."""
    if selector is None or selector.is_empty():
        return False
    return bool(selector.position or selector.rank or selector.count)


def _small(mask: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    return cv2.resize((mask > 0).astype(np.uint8), size, interpolation=cv2.INTER_NEAREST) > 0


def _hist(hsv_small: np.ndarray, mask_small: np.ndarray) -> np.ndarray | None:
    if mask_small.sum() < 4:
        return None
    h = cv2.calcHist([hsv_small], [0, 1], mask_small.astype(np.uint8), [16, 8], [0, 180, 0, 256])
    return cv2.normalize(h, None, 1.0, 0, cv2.NORM_L1)


def _centroid(mask_small: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(mask_small)
    return np.array([xs.mean(), ys.mean()], np.float32) if len(xs) else np.zeros(2, np.float32)


def _shift(mask_small: np.ndarray, d: np.ndarray) -> np.ndarray:
    if not np.any(np.abs(d) >= 0.5):
        return mask_small
    m = np.float32([[1, 0, d[0]], [0, 1, d[1]]])
    h, w = mask_small.shape
    return cv2.warpAffine(mask_small.astype(np.uint8), m, (w, h), flags=cv2.INTER_NEAREST) > 0


@dataclass
class _Track:
    mask: np.ndarray  # 축소 마스크 (bool) — 마지막으로 본 모습
    hist: np.ndarray | None
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2, np.float32))
    lost: int = 0
    area: float = 0.0  # 다 보일 때의 면적 (축소 기준)
    offset: np.ndarray = field(default_factory=lambda: np.zeros(2, np.float32))  # 마지막으로 다 본 뒤 예측으로 옮긴 양
    since: int = 0  # 마지막으로 다 본 뒤 지난 프레임 수
    target: bool = True  # 고른 대상인지 (아니면 헷갈리지 않게 같이 따라가는 다른 사람)

    def predicted(self) -> np.ndarray:
        return _shift(self.mask, self.offset + self.velocity)

    def coast(self) -> None:
        """이번 프레임은 제대로 못 봤다 — 예측대로 한 칸 옮긴다."""
        self.offset = self.offset + self.velocity
        self.since += 1


@dataclass
class InstanceTracker:
    selector: InstanceSelector
    tracks: List[_Track] = field(default_factory=list)  # 고른 대상 + 나머지 사람들 (target 으로 구분)
    reselected: int = 0  # selector 로 (다시) 고른 횟수 — 처음 1 + 놓쳐서 다시 고른 횟수
    lost_frames: int = 0  # 고른 대상을 하나라도 못 찾은 프레임 수
    reidentified: int = 0  # 오래 놓친 뒤 색으로 다시 찾은 횟수
    reacquired: int = 0  # 오래 놓친 뒤 새로 나타난 사람 중 selector 로 이어 간 횟수

    def choose(self, instances: List[Instance], frame: np.ndarray) -> List[Instance]:
        if not instances:
            self._age_all()
            return []
        h, w = frame.shape[:2]
        scale = min(1.0, TRACK_SIDE / max(h, w))
        size = (max(1, int(w * scale)), max(1, int(h * scale)))
        hsv = cv2.cvtColor(cv2.resize(frame, size, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
        smalls = [_small(i.mask, size) for i in instances]
        hists = [_hist(hsv, s) for s in smalls]

        if not any(t.target for t in self.tracks):
            return self._reselect(instances, frame, smalls, hists)

        pairs = []  # (점수, 추적 번호, 인스턴스 번호)
        for ti, track in enumerate(self.tracks):
            pred = track.predicted()
            for ii, s in enumerate(smalls):
                inter = np.logical_and(pred, s).sum()
                if not inter:
                    continue
                iou = inter / max(1, np.logical_or(pred, s).sum())
                if iou < MIN_IOU:
                    continue
                look = 0.5
                if track.hist is not None and hists[ii] is not None:
                    look = 1.0 - float(cv2.compareHist(track.hist, hists[ii], cv2.HISTCMP_BHATTACHARYYA))
                    if look < MIN_LOOK:
                        continue
                pairs.append((iou * (1 - APPEARANCE_WEIGHT) + look * APPEARANCE_WEIGHT, ti, ii))
        # 점수 높은 짝부터 — 앞을 지나가는 다른 사람은 그 사람의 추적이 먼저 가져가므로 고른 대상으로 넘어오지 않는다
        pairs.sort(reverse=True)
        used_i, matched = set(), {}
        for _score, ti, ii in pairs:
            if ti in matched or ii in used_i:
                continue
            used_i.add(ii)
            matched[ti] = ii
        # 못 찾은 고른 대상은 예측 위치 근처에 남은 인스턴스(가려졌다 조각으로 다시 보이는 중)와 한 번 더 — 겹치기만 하고 색이 비슷하면
        for ti, track in enumerate(self.tracks):
            if not track.target or ti in matched:
                continue
            near = cv2.dilate(track.predicted().astype(np.uint8), np.ones((REACQUIRE_PX * 2 + 1,) * 2, np.uint8)) > 0
            best = None
            for ii, s in enumerate(smalls):
                if ii in used_i or not np.logical_and(near, s).any():
                    continue
                look = 0.5
                if track.hist is not None and hists[ii] is not None:
                    look = 1.0 - float(cv2.compareHist(track.hist, hists[ii], cv2.HISTCMP_BHATTACHARYYA))
                if look >= MIN_LOOK and (best is None or look > best[0]):
                    best = (look, ii)
            if best is not None:
                used_i.add(best[1])
                matched[ti] = best[1]

        for ti, track in enumerate(self.tracks):
            if ti in matched:
                s = smalls[matched[ti]]
                area = float(s.sum())
                grown = area > MERGED * max(track.area, 1.0)
                # 커졌어도 다른 추적 대상과 겹치지 않으면 합쳐진 게 아니라 다가오거나 다시 들어오는 중이다 (기준 모습을 갱신해야 한다)
                # 겹친 상대도 사람 크기여야 한다 — 근처의 작은 오검출 추적과 겹친 것은 합쳐짐이 아니다 (DAVIS walking)
                merged = grown and any(
                    o.area >= 0.25 * area and np.logical_and(o.predicted(), s).sum() > 0.2 * o.area
                    for o in self.tracks if o is not track
                )
                if PARTIAL * track.area <= area and not merged:
                    step = (_centroid(s) - _centroid(track.mask)) / (track.since + 1)  # 가려졌던 동안의 평균 이동
                    track.velocity = _clamp(0.5 * track.velocity + 0.5 * step, MAX_SPEED * max(s.shape))
                    track.mask = s
                    track.offset = np.zeros(2, np.float32)
                    track.since = 0
                    track.area = 0.7 * track.area + 0.3 * area if track.area else area
                    if hists[matched[ti]] is not None:
                        track.hist = hists[matched[ti]]
                else:
                    track.coast()  # 일부 가려짐 · 옆 사람과 합쳐짐 — 다 보이던 모습을 예측 위치로 옮겨 둔다
                track.lost = 0
            else:
                track.lost += 1
                track.coast()
                track.velocity *= VELOCITY_DECAY
        targets = [ti for ti, t in enumerate(self.tracks) if t.target]
        if any(ti not in matched for ti in targets):
            self.lost_frames += 1
        if all(self.tracks[ti].lost > MAX_LOST for ti in targets):
            again = self._reidentify(targets, smalls, hists, used_i)
            if again is None:
                again = self._newcomer(targets, instances, frame, smalls, used_i)
            if again is not None:
                matched[targets[0]] = again
                used_i.add(again)
            elif all(self.tracks[ti].lost > RESELECT_LOST for ti in targets):
                return self._reselect(instances, frame, smalls, hists)
        chosen = [instances[matched[ti]] for ti in targets if ti in matched]
        # 새로 보인 사람은 "다른 사람" 추적으로 — 고른 대상과 헷갈리지 않게. 고른 대상과 크게 겹치면 같은 사람의 중복 검출이라 만들지 않는다
        target_masks = [smalls[matched[ti]] for ti in targets if ti in matched]
        for ii in range(len(instances)):
            if ii not in used_i and not any(_duplicate(smalls[ii], m) for m in target_masks):
                self.tracks.append(_new_track(smalls[ii], hists[ii], target=False))
        self.tracks = [t for t in self.tracks if t.target or t.lost <= MAX_LOST]
        return chosen

    def _age_all(self) -> None:
        if any(t.target for t in self.tracks):
            self.lost_frames += 1
        for t in self.tracks:
            t.lost += 1
            t.coast()
            t.velocity *= VELOCITY_DECAY
        # 오래 놓쳐도 지우지 않는다 — 다음에 검출이 있으면 색으로 다시 찾아보고(_reidentify), 없으면 selector 로 다시 고른다

    def _reidentify(self, targets, smalls, hists, used_i) -> int | None:
        """오래 놓친 고른 대상(하나일 때)을 색 분포로 다시 찾는다 — 다른 사람 추적이 가져가지 않은 인스턴스 중 가장 비슷한 것."""
        if len(targets) != 1:
            return None
        track = self.tracks[targets[0]]
        if track.hist is None:
            return None
        best = None
        for ii, h in enumerate(hists):
            if ii in used_i or h is None:
                continue
            look = 1.0 - float(cv2.compareHist(track.hist, h, cv2.HISTCMP_BHATTACHARYYA))
            if look >= REID_LOOK and (best is None or look > best[0]):
                best = (look, ii)
        if best is None:
            return None
        s = smalls[best[1]]
        track.mask, track.area, track.lost, track.since = s, float(s.sum()), 0, 0
        track.offset = np.zeros(2, np.float32)
        track.velocity = np.zeros(2, np.float32)
        self.reidentified += 1
        return best[1]

    def _newcomer(self, targets, instances, frame, smalls, used_i) -> int | None:
        """오래 놓친 대상이 색으로도 안 잡히면(일부만 보이며 다시 들어오는 중) — 이미 따라가는 다른 사람이 아닌
        **새로 나타난** 인스턴스 중 selector 가 고르는 것으로 이어 간다. 아는 다른 사람으로 넘어가지 않게 그들은 후보에서 뺀다.
        (실제 영상 DAVIS walking: 대상이 17프레임 사라졌다 작게 다시 들어올 때 직전 자리를 계속 들고 있던 문제)"""
        if len(targets) != 1:
            return None
        track = self.tracks[targets[0]]
        fresh = [ii for ii in range(len(instances)) if ii not in used_i and smalls[ii].sum() >= NEWCOMER_MIN * track.area]
        if not fresh:
            return None
        pick = select_instances([instances[ii] for ii in fresh], self.selector, frame).chosen
        if not pick:
            return None
        ii = next(k for k in fresh if instances[k] is pick[0])
        s = smalls[ii]
        track.mask, track.area, track.lost, track.since = s, float(s.sum()), 0, 0
        track.offset = np.zeros(2, np.float32)
        track.velocity = np.zeros(2, np.float32)
        self.reacquired += 1
        return ii

    def _reselect(self, instances, frame, smalls, hists) -> List[Instance]:
        chosen = select_instances(instances, self.selector, frame).chosen
        picked = {id(c) for c in chosen}
        chosen_masks = [smalls[k] for k, inst in enumerate(instances) if id(inst) in picked]
        self.tracks = [
            _new_track(smalls[k], hists[k], target=id(inst) in picked)
            for k, inst in enumerate(instances)
            # 고른 대상과 크게 겹치는 다른 마스크는 같은 사람의 중복 검출 — 따로 추적하면 다음 프레임에 대상을 빼앗는다
            if id(inst) in picked or not any(_duplicate(smalls[k], m) for m in chosen_masks)
        ]
        self.reselected += 1
        return chosen


def _clamp(v: np.ndarray, limit: float) -> np.ndarray:
    n = float(np.hypot(*v))
    return v if n <= limit else (v * (limit / n)).astype(np.float32)


def _duplicate(a: np.ndarray, b: np.ndarray) -> bool:
    small = min(int(a.sum()), int(b.sum()))
    return small > 0 and np.logical_and(a, b).sum() > DUPLICATE * small


def _new_track(mask_small: np.ndarray, hist: np.ndarray | None, *, target: bool) -> _Track:
    return _Track(mask=mask_small, hist=hist, area=float(mask_small.sum()), target=target)
