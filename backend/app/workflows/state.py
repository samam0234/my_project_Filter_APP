"""GraphState shared across LangGraph nodes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    # identity
    job_id: str

    # input
    image_bytes: bytes
    image_path: Optional[str]
    prompt: str

    # prompt analysis
    parsed_prompt: Dict[str, Any]

    # images (serialized paths or kept in-memory via private cache in runner)
    # ndarray not stored in TypedDict for JSON safety — runner holds images
    status: str  # pending | ok | fallback | failed
    error: Optional[str]
    quality_score: float
    confidences: List[float]
    labels: List[str]
    backend: str

    # artifacts
    before_path: Optional[str]
    after_path: Optional[str]
    feedback_saved: bool
    feedback_meta: Dict[str, Any]

    # control
    retry_count: int
    message: str
