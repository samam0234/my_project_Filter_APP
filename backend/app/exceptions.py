"""애플리케이션 예외 정의."""

from fastapi import HTTPException, status


class CutAndKeepError(Exception):
    """애플리케이션 기본 예외."""

    def __init__(self, message: str = "예기치 않은 오류") -> None:
        self.message = message
        super().__init__(message)


class FileValidationError(CutAndKeepError):
    """업로드 검증 실패 (MIME, 크기, 확장자)."""


class PipelineError(CutAndKeepError):
    """이미지 처리 / 워크플로 실패."""


class ModelNotReadyError(CutAndKeepError):
    """모델 가중치 없음 또는 로드 실패."""


def to_http_exception(exc: CutAndKeepError) -> HTTPException:
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
