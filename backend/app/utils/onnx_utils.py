"""Phase 1 YOLO-seg 추론용 ONNX Runtime 헬퍼.

Segmentor 가 Ultralytics .pt 로드에 실패했을 때
.onnx 세션 생성을 시도하는 경로에서 사용한다.

현재는 세션 생성·입력 이름 조회까지만 제공하고,
실제 전처리/후처리 추론 루프는 확장 지점이다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from loguru import logger


def create_session(model_path: Path | str, providers: Optional[list[str]] = None) -> Any:
    """모델 파일이 있으면 onnxruntime InferenceSession 생성.

    파일이 없거나 onnxruntime 미설치 시 None (호출측이 stub 으로 폴백).
    providers 기본: CPUExecutionProvider.
    """
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
    """세션 첫 번째 입력 텐서 이름 (보통 'images')."""
    return session.get_inputs()[0].name
