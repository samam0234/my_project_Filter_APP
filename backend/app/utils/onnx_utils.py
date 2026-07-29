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


# ---
# 제목 (하드코딩 파트 부분 : [ONNX 전처리·후처리 추론 루프])
# [관련 작업 임무 및 역할]
#   create_session 으로 만든 세션에 이미지를 넣고 마스크/박스 출력을 꺼낸다.
#   segmentation.Segmentor 의 ONNX 경로에서 호출할 헬퍼를 여기 둔다.
# [기능하고 연결된 변수 및 함수]
#   - create_session, session_input_name
#   - 호출측: app.services.segmentation.Segmentor (작성할 _predict_onnx)
#   - 입력: BGR ndarray, session
#   - 출력 예: masks(list), class_ids, confidences (프로젝트 합의 형식)
# [작성해야 하는 방식 및 규칙]
#   1) export 한 YOLO-seg ONNX 의 입출력 이름을 로그로 확인 후 맞출 것.
#   2) 전처리: resize/letterbox, BGR→RGB, /255, NCHW float32 등이 일반적.
#   3) 후처리: 원본 h,w 로 마스크 리사이즈, conf 임계, 클래스 이름 매핑은 호출측.
#   4) GPU provider 는 환경에 있을 때만 추가 (기본 CPU).
# [코드 방식 힌트]
#   def run_yolo_seg_onnx(session, image_bgr) -> tuple[...]:
#       name = session_input_name(session)
#       blob = preprocess(image_bgr)  # 직접 작성
#       outs = session.run(None, {name: blob})
#       return postprocess(outs, image_bgr.shape[:2])
# ---
