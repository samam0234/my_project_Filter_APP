"""업로드 보안: MIME, 확장자, 크기 검증."""

from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.constants import ALLOWED_EXTENSIONS
from app.exceptions import FileValidationError


def validate_extension(filename: str | None) -> str:
    if not filename:
        raise FileValidationError("파일명이 필요합니다.")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"확장자 '{ext}' 는 허용되지 않습니다. "
            f"허용: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_mime(content_type: str | None, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if not content_type:
        raise FileValidationError("Content-Type이 필요합니다.")
    mime = content_type.split(";")[0].strip().lower()
    if mime not in settings.allowed_mime_list:
        raise FileValidationError(
            f"MIME 타입 '{mime}' 는 허용되지 않습니다. "
            f"허용: {', '.join(settings.allowed_mime_list)}"
        )
    return mime


async def validate_upload_file(
    file: UploadFile,
    settings: Settings | None = None,
) -> bytes:
    """업로드 파일을 검증하고 바이트를 읽는다. 실패 시 즉시 거부."""
    settings = settings or get_settings()
    validate_extension(file.filename)
    validate_mime(file.content_type, settings)

    data = await file.read()
    if not data:
        raise FileValidationError("빈 파일입니다.")
    if len(data) > settings.max_upload_bytes:
        raise FileValidationError(
            f"파일이 최대 크기를 초과합니다: {settings.max_upload_size_mb}MB."
        )
    return data
