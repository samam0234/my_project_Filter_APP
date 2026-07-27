"""Upload security: MIME type, extension, and size validation."""

from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.constants import ALLOWED_EXTENSIONS
from app.exceptions import FileValidationError


def validate_extension(filename: str | None) -> str:
    if not filename:
        raise FileValidationError("Filename is required.")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Extension '{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_mime(content_type: str | None, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if not content_type:
        raise FileValidationError("Content-Type is required.")
    mime = content_type.split(";")[0].strip().lower()
    if mime not in settings.allowed_mime_list:
        raise FileValidationError(
            f"MIME type '{mime}' is not allowed. "
            f"Allowed: {', '.join(settings.allowed_mime_list)}"
        )
    return mime


async def validate_upload_file(
    file: UploadFile,
    settings: Settings | None = None,
) -> bytes:
    """Validate and read upload bytes. Rejects invalid files immediately."""
    settings = settings or get_settings()
    validate_extension(file.filename)
    validate_mime(file.content_type, settings)

    data = await file.read()
    if not data:
        raise FileValidationError("Empty file.")
    if len(data) > settings.max_upload_bytes:
        raise FileValidationError(
            f"File exceeds max size of {settings.max_upload_size_mb}MB."
        )
    return data
