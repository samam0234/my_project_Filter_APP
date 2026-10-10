"""애플리케이션 예외 정의.

도메인 예외 → HTTPException 변환 한곳 (to_http_exception).
라우터는 비즈니스 예외를 raise 하고, HTTP 상태 코드는 여기서만 결정한다.
"""

from fastapi import HTTPException, status


class CutAndKeepError(Exception):
    """애플리케이션 기본 예외.

    message 는 클라이언트 detail 및 로그에 그대로 쓸 수 있는 한국어 메시지.
    """

    def __init__(self, message: str = "예기치 않은 오류") -> None:
        self.message = message
        super().__init__(message)


class FileValidationError(CutAndKeepError):
    """업로드 검증 실패 (MIME, 크기, 확장자) → 보통 400."""


class PipelineError(CutAndKeepError):
    """이미지 처리 / 워크플로 실패 → 보통 422."""


class ModelNotReadyError(CutAndKeepError):
    """모델 가중치 없음 또는 로드 실패 → 보통 503."""


def to_http_exception(exc: CutAndKeepError) -> HTTPException:
    """도메인 예외를 FastAPI HTTPException 으로 매핑.

    FileValidationError → 400
    ModelNotReadyError  → 503
    PipelineError       → 422
    그 외 CutAndKeepError → 500
    """
    if isinstance(exc, FileValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, ModelNotReadyError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        )
    if isinstance(exc, PipelineError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=exc.message,
    )
