"""세그멘테이션 백엔드. Phase 1: YOLO-seg (ONNX/Ultralytics). Phase 2: DINO+SAM2."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from app.core.config import Settings, get_settings
from app.services.prompt_spec import STUFF_CLASSES
from app.utils.onnx_utils import class_names, create_session, run_yolo_seg_onnx


# 【수동】 라벨 별칭 — 프롬프트 어휘(COCO)와 서빙 모델 names 가 다를 때 양방향으로 맞춘다.
# 예: 5클래스 커스텀 모델은 "bag", LLM/LoRA 는 COCO "handbag"/"backpack"
LABEL_ALIASES: dict[str, set[str]] = {
    "bag": {"handbag", "backpack", "suitcase"},
    "cell phone": {"phone", "mobile phone"},
    "person": {"people", "human"},
}


def expand_targets(targets: set[str]) -> set[str]:
    """요청 라벨에 별칭을 더한다 (canonical ↔ 별칭 양방향)."""
    out = set(targets)
    for canon, alts in LABEL_ALIASES.items():
        if canon in targets:
            out |= alts
        if targets & alts:
            out.add(canon)
    return out


@dataclass(eq=False)  # 마스크 배열 비교 방지 — 동일성(is)으로만 비교
class Instance:
    """세그 인스턴스 1개 (요청 대상 필터 통과분).

    mask: 0/255 단일 채널 (입력 이미지와 같은 크기)
    bbox: (x0, y0, x1, y1) 픽셀, 마스크 기준
    """

    mask: np.ndarray
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]

    @property
    def area(self) -> int:
        return int(np.count_nonzero(self.mask))

    @classmethod
    def from_mask(cls, mask: np.ndarray, label: str, confidence: float) -> "Instance":
        ys, xs = np.where(mask > 0)
        bbox = (
            (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            if len(xs)
            else (0, 0, 0, 0)
        )
        return cls(mask=mask, label=label, confidence=confidence, bbox=bbox)


def union_mask(instances: List[Instance], shape: Tuple[int, int]) -> np.ndarray:
    """인스턴스 마스크 OR 합집합 (없으면 빈 마스크)."""
    union = np.zeros(shape, dtype=np.uint8)
    for inst in instances:
        union = cv2.bitwise_or(union, inst.mask)
    return union


@dataclass
class SegmentationResult:
    """세그 추론 결과.

    mask: 0/255 단일 채널 합집합 마스크
    confidences / labels: 마스크에 포함된(요청 대상) 인스턴스별 메타
    detected: 필터 전 모델이 감지한 전체 라벨 (대상 못 찾음 안내·피드백용)
    instances: 대상 인스턴스별 마스크 — instance_selector 가 이 중 일부를 고른다
    backend: "yolo" | "stub" 등 어떤 경로로 만들었는지
    """

    mask: np.ndarray
    confidences: List[float] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    backend: str = "stub"
    detected: List[str] = field(default_factory=list)
    instances: List[Instance] = field(default_factory=list)


class Segmentor:
    """Phase 게이트 세그멘터. Phase 1은 YOLO, Phase 2에서 백엔드 교체 가능."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session = None  # ONNX 세션 (선택)
        self._onnx_names: Optional[dict[int, str]] = None  # ONNX 메타데이터의 클래스 이름 (첫 추론 때 읽음)
        self._yolo = None  # Ultralytics YOLO 객체 (선택)
        self._ready = False
        self._lock = threading.Lock()
        self._stuff = None  # 배경 덩어리 세그(SegFormer ONNX) — 첫 사용 때 만든다
        self._stuff_lock = threading.Lock()
        self._init_backend()

    def stuff_segmenter(self):
        """건물·하늘·도로 같은 덩어리용 세그 (파일이 없거나 꺼져 있으면 available=False 인 객체)."""
        if self._stuff is None:
            with self._stuff_lock:
                if self._stuff is None:
                    from app.services.stuff_segmentation import StuffSegmenter

                    self._stuff = StuffSegmenter(self.settings)
        return self._stuff

    def warmup_stuff(self) -> bool:
        """기동 때 모델을 올리고 빈 이미지로 한 번 추론 (첫 요청 지연 방지). 못 쓰면 False."""
        stuff = self.stuff_segmenter()
        if not stuff.available:
            return False
        stuff.predict(np.zeros((480, 640, 3), np.uint8), ["sky"])
        return True

    def _predict_stuff(
        self,
        image: np.ndarray,
        targets: List[str],
        min_confidence: Optional[float],
    ) -> "SegmentationResult":
        """덩어리 대상(건물·하늘…)은 SegFormer 로, 섞여 있는 낱개 물체(사람·차…)는 기존 경로로 → 합친다."""
        stuff_targets = [t for t in targets if t in STUFF_CLASSES]
        others = [t for t in targets if t not in STUFF_CLASSES]
        mask, comps = self.stuff_segmenter().predict(image, stuff_targets)
        instances = [Instance(mask=m, label=lab, confidence=conf, bbox=box) for m, lab, conf, box in comps]
        present = [g for g in stuff_targets if any(i.label == g for i in instances)]
        result = SegmentationResult(
            mask=mask,
            confidences=[i.confidence for i in instances],
            labels=[i.label for i in instances],
            backend="segformer",
            detected=present,
            instances=instances,
        )
        if not others:
            return result
        base = self.predict(image, others, min_confidence)
        return SegmentationResult(
            mask=cv2.bitwise_or(base.mask, result.mask) if base.mask.shape == result.mask.shape else result.mask,
            confidences=[*base.confidences, *result.confidences],
            labels=[*base.labels, *result.labels],
            backend=f"{base.backend}+segformer",
            detected=[*base.detected, *result.detected],
            instances=[*base.instances, *result.instances],
        )

    def _init_backend(self) -> None:
        """설정 경로의 가중치를 로드. 없으면 stub 모드로 둔다."""
        model_path = self.settings.yolo_model_file

        # =============================================================================
        # [이미 구현된 구간 · 바이브] Ultralytics .pt 로드
        # -----------------------------------------------------------------------------
        # 가중치 파일 배치(.env YOLO_MODEL_PATH)는 코드 밖 작업.
        # 서비스 본선: instance segmentation (yolo26m-seg). detect 전용 .pt 금지.
        # =============================================================================
        prefer_onnx = self.settings.seg_prefer_onnx and model_path.suffix.lower() == ".onnx"
        if not prefer_onnx and model_path.suffix.lower() in {".pt", ".onnx"} and model_path.exists():
            try:
                from ultralytics import YOLO

                self._yolo = YOLO(str(model_path))
                self._ready = True
                logger.info("YOLO 세그멘터 준비: {}", model_path)
                return
            except Exception as exc:
                logger.warning("Ultralytics 로드 실패: {}", exc)

        # =============================================================================
        # [하드코딩 파트] ONNX 세션 준비 후 추론 연결
        # -----------------------------------------------------------------------------
        # [임무] .pt 실패/미사용 시 .onnx 로 세그 가능 (Docker 경량 축)
        # [연결] create_session → self._session / predict 의 ONNX 분기 / onnx_utils
        # [규칙] 세션만 만들고 predict 미연결이면 stub. 실패 시 _stub_mask.
        # [힌트] self._session = create_session(...); # + _predict_onnx 작성
        # =============================================================================
        # ONNX 는 create_session 으로 열고, 추론은 _predict_onnx (onnx_utils.run_yolo_seg_onnx) 가 한다.
        # SEG_PREFER_ONNX=true 면 ultralytics 가 설치돼 있어도 이 경로 (CPU 에서 torch 없이 가볍게).

        # =============================================================================
        # [이미 구현된 구간 · 바이브] ONNX 세션 생성 시도 + 미준비 경고
        # =============================================================================
        self._session = create_session(model_path)
        self._ready = self._session is not None
        if not self._ready:
            logger.warning(
                "세그 모델 없음. 중앙 stub 마스크 사용. "
                "가중치 경로: {}",
                model_path,
            )

    @property
    def ready(self) -> bool:
        """모델이 실제로 로드되었는지."""
        return self._ready

    def predict(
        self,
        image: np.ndarray,
        targets: Optional[List[str]] = None,
        min_confidence: Optional[float] = None,
    ) -> SegmentationResult:
        """요청 대상에 대한 인스턴스 마스크 합집합 반환.

        min_confidence: 이번 호출만 쓸 신뢰도 기준 (재시도 시 완화). None 이면 Settings 값.
        """
        targets = targets or ["person"]

        # 건물·하늘·도로… 덩어리는 YOLO(COCO)가 모른다 → SegFormer. 모델 파일이 없으면 아래 기존 흐름(빈 결과)
        if any(t in STUFF_CLASSES for t in targets) and self.stuff_segmenter().available:
            return self._predict_stuff(image, targets, min_confidence)

        # 닫힌 어휘에 없는 대상만. 실패·미설치·빈 검출은 YOLO/ONNX/stub 으로 이어진다.
        if self._needs_open_vocab(targets):
            try:
                opened = predict_grounding_sam2(
                    image,
                    ", ".join(targets),
                    settings=self.settings,
                )
                if opened.mask.any() or (self._yolo is None and self._session is None):
                    return opened
                logger.info("오픈보캐브 검출 없음 — 닫힌 어휘 세그로 계속")
            except Exception as exc:
                logger.warning("오픈보캐브 세그 생략: {}", exc)

        # =============================================================================
        # [이미 구현된 구간 · 바이브] YOLO .pt 경로 우선
        # =============================================================================
        if self._yolo is not None:
            # Ultralytics 모델은 스레드 안전이 보장되지 않음 — 업로드가 스레드풀에서 동시에 돌 수 있으므로 직렬화
            with self._lock:
                return self._predict_yolo(image, targets, min_confidence)

        # =============================================================================
        # [하드코딩 파트] ONNX predict 분기
        # -----------------------------------------------------------------------------
        # [임무] self._session 있을 때 YOLO-seg ONNX 결과 반환
        # [연결] self._session, _stub_mask, (작성) _predict_onnx, onnx_utils
        # [규칙] 반환=SegmentationResult, backend="onnx", target 필터는 yolo 와 동일 권장
        # [힌트] if self._session is not None: return self._predict_onnx(image, targets)
        # =============================================================================
        if self._session is not None:
            try:
                return self._predict_onnx(image, targets, min_confidence)
            except Exception as exc:  # 추론 오류가 요청 전체를 막지 않게 — stub 이 아니라 실패를 드러내려면 예외 유지
                logger.exception("ONNX 추론 실패: {}", exc)
                raise

        # =============================================================================
        # [이미 구현된 구간 · 바이브] 모델 없을 때 stub 마스크
        # =============================================================================
        return self._stub_mask(image, targets)

    def _known_labels(self) -> set[str]:
        """로드된 YOLO/ONNX 클래스 이름. 모델이 없으면 빈 집합."""
        raw = None
        if self._yolo is not None:
            raw = getattr(self._yolo, "names", None)
        elif self._onnx_names:
            raw = self._onnx_names
        if isinstance(raw, dict):
            return {str(value).lower() for value in raw.values()}
        return set()

    def _needs_open_vocab(self, targets: List[str]) -> bool:
        """OPEN_VOCAB_ENABLED 이고, 요청 중 모델 클래스 밖 이름이 있을 때만."""
        if not self.settings.open_vocab_enabled:
            return False
        wanted = {item.lower() for item in targets if item}
        if not wanted or "all" in wanted:
            return False
        known = self._known_labels()
        if not known:
            return True
        return any(item not in expand_targets(known) for item in expand_targets(wanted))

    def _predict_onnx(
        self,
        image: np.ndarray,
        targets: List[str],
        min_confidence: Optional[float] = None,
    ) -> SegmentationResult:
        """onnxruntime 추론 → _predict_yolo 와 같은 규칙으로 대상 라벨만 모아 SegmentationResult.

        신뢰도 기준은 모델 출력 단계에서 바로 적용 (ONNX 는 predict(conf=) 가 없음).
        """
        threshold = self.settings.min_confidence if min_confidence is None else min_confidence
        if self._onnx_names is None:
            self._onnx_names = class_names(self._session)
        names = self._onnx_names
        h, w = image.shape[:2]
        target_set = expand_targets({t.lower() for t in targets})
        keep_all = not target_set or "all" in target_set
        instances: List[Instance] = []
        detected: List[str] = []
        for cls_id, conf, binary in run_yolo_seg_onnx(self._session, image, threshold):
            label = str(names.get(cls_id, cls_id)).lower()
            detected.append(label)
            if not keep_all and label not in target_set:
                continue
            if binary.any():
                instances.append(Instance.from_mask(binary, label, conf))
        union = union_mask(instances, (h, w))
        if not union.any():
            logger.info("요청 대상 없음 targets={} detected={}", sorted(target_set), detected)
        return SegmentationResult(
            mask=union,
            confidences=[i.confidence for i in instances],
            labels=[i.label for i in instances],
            backend="onnx",
            detected=detected,
            instances=instances,
        )

    def _predict_yolo(
        self,
        image: np.ndarray,
        targets: List[str],
        min_confidence: Optional[float] = None,
    ) -> SegmentationResult:
        """Ultralytics predict → 클래스 필터 → 마스크 bitwise OR 합치기.

        - targets 에 있는 라벨만 합친다 ("all" 이면 전부)
        - confidence 가 min_confidence 미만인 인스턴스는 대상이어도 제외
        - 대상이 하나도 없으면 빈 마스크 반환 (stub 아님)
          → validator 가 failed 로 판정, 피드백으로 저장되어 학습 재료가 됨
        """
        # =============================================================================
        # [이미 구현된 구간 · 바이브] _predict_yolo 본문
        # -----------------------------------------------------------------------------
        # 하드코딩 숙제 아님. 튜닝( conf 필터, 0.5 임계 )만 필요 시 수정.
        # =============================================================================
        img = image.copy()
        threshold = self.settings.min_confidence if min_confidence is None else min_confidence
        # conf 를 넘겨야 재시도의 낮춘 기준이 실제로 적용된다 (Ultralytics 기본 conf=0.25 가 먼저 걸러 버림)
        # retina_masks: 마스크를 원본 해상도로 직접 계산 (기본은 letterbox 크기라 단순 확대하면 경계가 거칠어짐 —
        # 정답 폴리곤 대비 IoU 0.825 → 0.848, 속도 차이 없음. docs/plan/ONNX_INFERENCE.md)
        results = self._yolo.predict(img, verbose=False, conf=threshold, retina_masks=True)
        h, w = img.shape[:2]
        instances: List[Instance] = []
        detected: List[str] = []

        target_set = expand_targets({t.lower() for t in targets})
        keep_all = not target_set or "all" in target_set
        for r in results:
            names = r.names or {}
            if r.masks is None:
                continue
            masks = r.masks.data.cpu().numpy()
            boxes = r.boxes
            for i, m in enumerate(masks):
                cls_id = int(boxes.cls[i].item()) if boxes is not None else -1
                conf = float(boxes.conf[i].item()) if boxes is not None else 0.0
                label = str(names.get(cls_id, cls_id)).lower()
                if conf < threshold:
                    continue
                detected.append(label)
                if not keep_all and label not in target_set:
                    continue
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
                binary = (m_resized > 0.5).astype(np.uint8) * 255
                if binary.any():
                    instances.append(Instance.from_mask(binary, label, conf))

        union = union_mask(instances, (h, w))
        if not union.any():
            logger.info("요청 대상 없음 targets={} detected={}", sorted(target_set), detected)

        return SegmentationResult(
            mask=union,
            confidences=[i.confidence for i in instances],
            labels=[i.label for i in instances],
            backend="yolo",
            detected=detected,
            instances=instances,
        )

    def _stub_mask(
        self,
        image: np.ndarray,
        targets: List[str],
    ) -> SegmentationResult:
        """스캐폴드/데모용 중앙 타원 stub 마스크.

        모델 없이도 upload → 효과 파이프라인을 돌려 보기 위함.
        """
        # =============================================================================
        # [이미 구현된 구간 · 바이브] stub 타원 마스크
        # =============================================================================
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (max(1, w // 4), max(1, h // 3))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        logger.debug("stub 세그 마스크 사용 targets={}", targets)
        return SegmentationResult(
            mask=mask,
            confidences=[0.5],
            labels=targets,
            backend="stub",
        )


# =============================================================================
# [하드코딩 파트] Grounding DINO + SAM2 백엔드
# -----------------------------------------------------------------------------
# [임무] Phase2 오픈보캐브 세그 (텍스트 → 정밀 마스크)
# [연결] Segmentor.predict 분기 후보, SegmentationResult, training 의존성 분리
# [규칙] Phase1 YOLO 안정 후. DINO 박스 → SAM2. 절대경로 금지.
# [힌트] boxes=dino...; masks=sam2...; return SegmentationResult(..., backend="dino_sam2")
# =============================================================================
_OV_CACHE: dict[str, tuple] = {}


def _dino_text(prompt: str) -> str:
    """Grounding DINO 는 'dog . cat .' 형태를 기대한다."""
    parts = [part.strip() for part in prompt.replace(",", ".").split(".") if part.strip()]
    if not parts:
        parts = [prompt.strip()] if prompt.strip() else ["object"]
    return " . ".join(parts) + " ."


def _load_local_pair(kind: str, model_id: str, model_cls, processor_cls):
    """local_files_only. 허브 다운로드는 하지 않는다."""
    key = f"{kind}:{model_id}"
    if key in _OV_CACHE:
        return _OV_CACHE[key]
    try:
        processor = processor_cls.from_pretrained(model_id, local_files_only=True)
        model = model_cls.from_pretrained(model_id, local_files_only=True)
    except Exception as exc:
        raise NotImplementedError(
            f"{kind} 가중치를 로컬에서 열 수 없습니다 ({model_id}): {exc}"
        ) from exc
    _OV_CACHE[key] = (processor, model)
    return processor, model


def _post_dino(processor, outputs, inputs, box_threshold: float, text_threshold: float, hw: Tuple[int, int]):
    """transformers 버전마다 인자 이름이 다르다."""
    attempts = (
        {
            "outputs": outputs,
            "input_ids": inputs.input_ids,
            "threshold": box_threshold,
            "text_threshold": text_threshold,
            "target_sizes": [hw],
        },
        {
            "outputs": outputs,
            "input_ids": inputs.input_ids,
            "box_threshold": box_threshold,
            "text_threshold": text_threshold,
            "target_sizes": [hw],
        },
    )
    last: Exception | None = None
    for kwargs in attempts:
        try:
            return processor.post_process_grounded_object_detection(**kwargs)
        except TypeError as exc:
            last = exc
    raise NotImplementedError(f"Grounding DINO 후처리 시그니처 불일치: {last}")


def _keep_matched(boxes: list, scores: list, labels: list[str]):
    """요청 문구와 이어지지 않은 박스(빈 라벨)는 버린다.

    DINO 는 박스 점수가 임계값을 넘어도 문구 토큰 점수가 낮으면 라벨을 빈 문자열로 준다 —
    "무언가 있긴 한데 요청한 그것은 아님" 이라 지우면 엉뚱한 영역이 지워진다.
    """
    keep = [i for i, label in enumerate(labels) if label.strip()]
    if len(keep) == len(boxes):
        return boxes, scores, labels
    return (
        [boxes[i] for i in keep],
        [scores[i] for i in keep if i < len(scores)],
        [labels[i] for i in keep],
    )


def warmup_open_vocab(settings: Settings | None = None) -> bool:
    """DINO·SAM2 를 미리 올리고 빈 이미지로 한 번 추론 (첫 요청 16초 → 1초). 꺼져 있거나 실패하면 False."""
    settings = settings or get_settings()
    if not settings.open_vocab_enabled:
        return False
    try:
        _infer_open_vocab(np.zeros((480, 640, 3), np.uint8), "object", settings)
        return True
    except Exception as exc:
        logger.warning("오픈보캐브 워밍업 실패 (첫 요청에서 다시 시도): {}", exc)
        return False


def _infer_open_vocab(
    image: np.ndarray,
    prompt: str,
    settings: Settings,
) -> SegmentationResult:
    """로컬 Grounding DINO 박스 → SAM2 마스크. 의존성·가중치가 없으면 NotImplementedError."""
    try:
        import torch
        from PIL import Image
        from transformers import (
            AutoModelForZeroShotObjectDetection,
            AutoProcessor,
            Sam2Model,
            Sam2Processor,
        )
    except ImportError as exc:
        raise NotImplementedError(f"open-vocab 의존성 없음: {exc}") from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dino_proc, dino_model = _load_local_pair(
        "dino",
        settings.dino_model_id,
        AutoModelForZeroShotObjectDetection,
        AutoProcessor,
    )
    sam_proc, sam_model = _load_local_pair(
        "sam2",
        settings.sam2_model_id,
        Sam2Model,
        Sam2Processor,
    )
    dino_model.to(device).eval()
    sam_model.to(device).eval()

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    inputs = dino_proc(images=pil, text=_dino_text(prompt), return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = dino_model(**inputs)
    height, width = image.shape[:2]
    threshold = float(settings.open_vocab_box_threshold)
    processed = _post_dino(
        dino_proc, outputs, inputs, threshold, float(settings.open_vocab_text_threshold), (height, width)
    )
    first = processed[0] if processed else {}
    boxes = first["boxes"].detach().cpu().tolist() if len(first.get("boxes", [])) else []
    scores = first["scores"].detach().cpu().tolist() if len(first.get("scores", [])) else []
    raw_labels = first.get("text_labels", first.get("labels", []))
    labels = [str(item).lower() for item in raw_labels] or ["object"] * len(boxes)
    boxes, scores, labels = _keep_matched(boxes, scores, labels)

    if not boxes:
        return SegmentationResult(
            mask=np.zeros((height, width), dtype=np.uint8),
            backend="dino_sam2",
            detected=[],
        )

    box_inputs = sam_proc(
        images=pil,
        input_boxes=[[[float(value) for value in box] for box in boxes]],
        return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        sam_out = sam_model(**box_inputs, multimask_output=False)
    pred = sam_out.pred_masks.detach().cpu()
    original_sizes = box_inputs.get("original_sizes")
    if original_sizes is not None and hasattr(sam_proc, "post_process_masks"):
        try:
            mask_arr = sam_proc.post_process_masks(pred, original_sizes.cpu())[0]
        except Exception:
            mask_arr = pred[0]
    else:
        mask_arr = pred[0]
    if hasattr(mask_arr, "numpy"):
        mask_arr = mask_arr.numpy()

    instances: List[Instance] = []
    detected = labels
    for index, _box in enumerate(boxes):
        mask = mask_arr[index]
        while getattr(mask, "ndim", 0) > 2:
            mask = mask[0]
        if tuple(mask.shape[:2]) != (height, width):
            mask = cv2.resize(mask.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR)
        binary = (mask > 0.0).astype(np.uint8) * 255
        confidence = float(scores[index]) if index < len(scores) else threshold
        label = detected[index] if index < len(detected) else "object"
        if binary.any():
            instances.append(Instance.from_mask(binary, label, confidence))
    union = union_mask(instances, (height, width))
    return SegmentationResult(
        mask=union,
        confidences=[item.confidence for item in instances],
        labels=[item.label for item in instances],
        backend="dino_sam2",
        detected=detected,
        instances=instances,
    )


def predict_grounding_sam2(
    image: np.ndarray,
    prompt: str,
    settings: Settings | None = None,
) -> SegmentationResult:
    """Phase 2: Grounding DINO + SAM2.

    OPEN_VOCAB_ENABLED 가 꺼져 있거나 로컬 가중치가 없으면 NotImplementedError.
    호출측(Segmentor.predict)은 그 경우 YOLO/ONNX/stub 으로 넘어간다.
    """
    settings = settings or get_settings()
    if not settings.open_vocab_enabled:
        raise NotImplementedError("OPEN_VOCAB_ENABLED 가 꺼져 있습니다.")
    text = (prompt or "").strip()
    if not text:
        raise NotImplementedError("오픈보캐브 프롬프트가 비어 있습니다.")
    return _infer_open_vocab(image, text, settings)
