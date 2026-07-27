"""ONNX Runtime helpers for Phase 1 YOLO-seg inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger


def create_session(model_path: Path | str, providers: Optional[list[str]] = None) -> Any:
    """Create an onnxruntime InferenceSession if the model file exists."""
    path = Path(model_path)
    if not path.exists():
        logger.warning("ONNX model not found: {}", path)
        return None

    try:
        import onnxruntime as ort
    except ImportError as exc:
        logger.error("onnxruntime not installed: {}", exc)
        return None

    if providers is None:
        providers = ["CPUExecutionProvider"]

    session = ort.InferenceSession(str(path), providers=providers)
    logger.info("Loaded ONNX model: {} providers={}", path, session.get_providers())
    return session


def session_input_name(session: Any) -> str:
    return session.get_inputs()[0].name
