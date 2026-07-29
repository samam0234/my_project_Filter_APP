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
    # =============================================================================
    # [이미 구현된 구간 · 바이브] InferenceSession 생성
    # =============================================================================
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
    # =============================================================================
    # [이미 구현된 구간 · 바이브] 입력 텐서 이름
    # =============================================================================
    return session.get_inputs()[0].name


# =============================================================================
# [하드코딩 파트] ONNX 전처리·후처리 추론 루프
# -----------------------------------------------------------------------------
# [임무] session + BGR 이미지 → 마스크/박스 출력 헬퍼
# [연결] create_session, session_input_name, Segmentor._predict_onnx (작성)
# [규칙] export YOLO-seg 입출력 이름 확인. letterbox·NCHW·리사이즈 후처리.
# [힌트]
#   def run_yolo_seg_onnx(session, image_bgr) -> tuple[...]:
#       name = session_input_name(session)
#       blob = preprocess(image_bgr)
#       outs = session.run(None, {name: blob})
#       return postprocess(outs, image_bgr.shape[:2])
# =============================================================================
# >>> 여기에 run_yolo_seg_onnx / preprocess / postprocess 작성 <<<
#