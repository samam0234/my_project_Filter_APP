"""Phase 1 YOLO-seg 추론용 ONNX Runtime 헬퍼."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger


def create_session(model_path: Path | str, providers: Optional[list[str]] = None) -> Any:
    """모델 파일이 있으면 onnxruntime InferenceSession 생성."""
    path = Path(model_path)
    if not path.exists():
        logger.warning("ONNX 모델 없음: {}", path)
        return None

    try:
        import onnxruntime as ort
    except ImportError as exc:
        logger.error("onnxruntime 미설치: {}", exc)
        return None

    if providers is None:
        providers = ["CPUExecutionProvider"]

    session = ort.InferenceSession(str(path), providers=providers)
    logger.info("ONNX 모델 로드: {} providers={}", path, session.get_providers())
    return session


def session_input_name(session: Any) -> str:
    return session.get_inputs()[0].name
