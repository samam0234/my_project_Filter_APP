"""LangGraph 노드 간 공유 GraphState."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    # 식별
    job_id: str

    # 입력
    image_bytes: bytes
    image_path: Optional[str]
    prompt: str

    # 프롬프트 분석
    parsed_prompt: Dict[str, Any]

    # 이미지 (경로 직렬화 또는 runner 전용 캐시)
    # JSON 안전을 위해 TypedDict에 ndarray 미저장 — runner가 보관
    status: str  # pending | ok | fallback | failed
    error: Optional[str]
    quality_score: float
    confidences: List[float]
    labels: List[str]
    backend: str

    # 산출물
    before_path: Optional[str]
    after_path: Optional[str]
    feedback_saved: bool
    feedback_meta: Dict[str, Any]

    # 제어
    retry_count: int
    message: str
