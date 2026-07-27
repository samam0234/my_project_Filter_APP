"""LangGraph node functions. Orchestration only — heavy work in services."""

from __future__ import annotations

import re
from typing import Any, Dict
from uuid import uuid4

from loguru import logger

from app.core.constants import JobStatus
from app.schemas.request import ParsedPrompt
from app.services.feedback_service import FeedbackService
from app.services.image_processor import ImageProcessor
from app.workflows.state import GraphState

# Module-level processor (lazy)
_processor: ImageProcessor | None = None
_feedback: FeedbackService | None = None
# In-memory image cache keyed by job_id (avoids putting ndarray in graph state)
_IMAGE_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_processor() -> ImageProcessor:
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


def _get_feedback() -> FeedbackService:
    global _feedback
    if _feedback is None:
        _feedback = FeedbackService()
    return _feedback


def parse_prompt_heuristic(prompt: str) -> ParsedPrompt:
    """
    Phase 1 fallback parser without LLM.
    Examples: '강아지만 남기고 배경 블러', 'person remove background'
    """
    text = prompt.lower().strip()
    effect = "remove_bg"
    crop = False
    intensity = 15

    if "blur" in text or "블러" in text:
        effect = "blur"
    if "crop" in text or "크롭" in text or "잘라" in text:
        effect = "crop"
        crop = True
    if "크롭" in text or "crop" in text:
        crop = True

    # intensity like "blur 20" / "강도 20"
    m = re.search(r"(?:intensity|강도|blur)\s*[:=]?\s*(\d{1,3})", text)
    if m:
        intensity = max(0, min(100, int(m.group(1))))

    # crude target extraction: quoted word or last known class keywords
    targets = []
    quoted = re.findall(r"[\"'“”](.+?)[\"'“”]", prompt)
    if quoted:
        targets = [q.strip() for q in quoted if q.strip()]
    else:
        keywords = [
            ("person", ["person", "사람", "인물"]),
            ("dog", ["dog", "강아지", "개"]),
            ("cat", ["cat", "고양이"]),
            ("car", ["car", "차", "자동차"]),
            ("bag", ["bag", "가방"]),
        ]
        for label, keys in keywords:
            if any(k in text for k in keys):
                targets.append(label)
    if not targets:
        targets = ["person"]

    return ParsedPrompt(target=targets, effect=effect, intensity=intensity, crop=crop)


def prompt_analyzer(state: GraphState) -> GraphState:
    """Node: natural language → structured ParsedPrompt (heuristic / LLM later)."""
    prompt = state.get("prompt") or ""
    job_id = state.get("job_id") or uuid4().hex
    parsed = parse_prompt_heuristic(prompt)
    logger.info("prompt_analyzer job={} parsed={}", job_id, parsed.model_dump())
    return {
        **state,
        "job_id": job_id,
        "parsed_prompt": parsed.model_dump(),
        "status": JobStatus.PENDING.value,
        "retry_count": state.get("retry_count") or 0,
    }


def preprocessor(state: GraphState) -> GraphState:
    """Node: decode + CLAHE preprocess (via ImageProcessor)."""
    job_id = state["job_id"]
    image_bytes = state.get("image_bytes")
    if not image_bytes:
        return {**state, "status": JobStatus.FAILED.value, "error": "No image_bytes"}

    processor = _get_processor()
    from app.utils.image_utils import decode_image_bytes

    original = decode_image_bytes(image_bytes)
    preprocessed = processor.preprocess(original)
    _IMAGE_CACHE[job_id] = {
        "original": original,
        "preprocessed": preprocessed,
        "image_bytes": image_bytes,
    }
    return {**state, "message": "preprocessed"}


def segmentor(state: GraphState) -> GraphState:
    """Node: run segmentation on preprocessed image."""
    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    pre = cache.get("preprocessed")
    if pre is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "Missing preprocessed image"}

    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    processor = _get_processor()
    seg = processor.segmentor.predict(pre, targets=parsed.target)
    cache["mask"] = seg.mask
    cache["seg"] = seg
    _IMAGE_CACHE[job_id] = cache
    return {
        **state,
        "confidences": seg.confidences,
        "labels": seg.labels,
        "backend": seg.backend,
        "message": "segmented",
    }


def validator_node(state: GraphState) -> GraphState:
    """Node: score mask quality."""
    from app.services.validator import score_mask

    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    mask = cache.get("mask")
    if mask is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "Missing mask"}

    confidences = state.get("confidences") or []
    result = score_mask(mask, confidences)
    return {
        **state,
        "status": result.status,
        "quality_score": result.quality_score,
        "message": result.message,
        "error": None if result.ok else result.message,
    }


def effect_applier(state: GraphState) -> GraphState:
    """Node: refine mask + apply blur/crop/remove_bg."""
    from app.services.effects import apply_effects, refine_mask
    from app.core.config import get_settings
    from app.utils.image_utils import ensure_dir, save_image

    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    original = cache.get("original")
    mask = cache.get("mask")
    if original is None or mask is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "Missing image/mask"}

    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    refined = refine_mask(mask, original)
    result_img = apply_effects(original, refined, parsed)
    cache["result"] = result_img
    _IMAGE_CACHE[job_id] = cache

    settings = get_settings()
    out_dir = settings.upload_path / job_id
    ensure_dir(out_dir)
    before_path = out_dir / "before.jpg"
    # BGRA → BGR for jpeg when needed
    after_img = result_img
    if after_img.ndim == 3 and after_img.shape[2] == 4:
        after_path = out_dir / "after.png"
    else:
        after_path = out_dir / "after.jpg"
    save_image(before_path, original)
    save_image(after_path, after_img)

    status = state.get("status") or JobStatus.OK.value
    if status == JobStatus.PENDING.value:
        status = JobStatus.OK.value

    return {
        **state,
        "before_path": str(before_path),
        "after_path": str(after_path),
        "status": status,
        "message": state.get("message") or "effects_applied",
    }


def feedback_collector(state: GraphState) -> GraphState:
    """Node: persist failed/fallback case (DB + file sidecar)."""
    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    original = cache.get("original")
    row, path = _get_feedback().save_failure(
        job_id=job_id,
        image=original,
        meta={
            "prompt": state.get("prompt"),
            "parsed_prompt": state.get("parsed_prompt"),
            "quality_score": state.get("quality_score"),
            "error": state.get("error"),
            "backend": state.get("backend"),
        },
    )
    return {
        **state,
        "feedback_saved": True,
        "feedback_meta": {
            "path": str(path) if path else None,
            "feedback_id": row.id if row else None,
        },
        "message": "feedback_saved",
    }


def clear_job_cache(job_id: str) -> None:
    _IMAGE_CACHE.pop(job_id, None)
