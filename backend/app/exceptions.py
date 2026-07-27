"""Application exceptions."""

from fastapi import HTTPException, status


class CutAndKeepError(Exception):
    """Base application error."""

    def __init__(self, message: str = "Unexpected error") -> None:
        self.message = message
        super().__init__(message)


class FileValidationError(CutAndKeepError):
    """Invalid upload (MIME, size, extension)."""


class PipelineError(CutAndKeepError):
    """Image processing / workflow failure."""


class ModelNotReadyError(CutAndKeepError):
    """Model weights missing or failed to load."""


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
