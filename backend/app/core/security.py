"""업로드 보안: MIME, 확장자, 크기, 내용 시그니처 검증.

라우터에서 파이프라인 진입 전에 호출한다.
실패 시 FileValidationError → HTTP 400 으로 변환.
"""

from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.constants import ALLOWED_EXTENSIONS
from app.exceptions import FileValidationError


def validate_extension(filename: str | None) -> str:
    """파일 확장자가 ALLOWED_EXTENSIONS 에 있는지 검사."""
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
    """Content-Type 이 설정 허용 MIME 목록에 있는지 검사."""
    settings = settings or get_settings()
    if not content_type:
        raise FileValidationError("Content-Type이 필요합니다.")
    # charset 등 파라미터 제거
    mime = content_type.split(";")[0].strip().lower()
    if mime not in settings.allowed_mime_list:
        raise FileValidationError(
            f"MIME 타입 '{mime}' 는 허용되지 않습니다. "
            f"허용: {', '.join(settings.allowed_mime_list)}"
        )
    return mime


# 파일 앞부분(매직 바이트)으로 실제 이미지인지 확인 — 확장자·Content-Type 은 클라이언트가 마음대로 보낼 수 있다.
_SIGNATURES = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
)


def validate_image_signature(data: bytes) -> str:
    """JPEG · PNG · WebP 시그니처가 아니면 FileValidationError. 반환: 형식 이름."""
    for magic, name in _SIGNATURES:
        if data.startswith(magic):
            return name
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WEBP"
    raise FileValidationError("이미지 파일이 아닙니다 (JPEG · PNG · WebP 만 가능).")


_MP4_BOXES = (b"ftyp", b"moov", b"mdat", b"wide", b"free", b"skip")  # MP4 · MOV 의 첫 박스


def validate_video_signature(data: bytes) -> str:
    """AVI · MP4/MOV · WebM/MKV 시그니처가 아니면 FileValidationError. 반환: 컨테이너 이름."""
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return "AVI"
    if len(data) >= 8 and data[4:8] in _MP4_BOXES:
        return "MP4"
    if data[:4] == bytes([0x1A, 0x45, 0xDF, 0xA3]):  # EBML
        return "WEBM"
    raise FileValidationError("영상 파일이 아닙니다 (mp4 · mov · avi · webm · mkv 만 가능).")


async def validate_upload_file(
    file: UploadFile,
    settings: Settings | None = None,
) -> bytes:
    """업로드 파일을 검증하고 바이트를 읽는다. 실패 시 즉시 거부.

    순서: 확장자 → MIME → 본문 읽기 → 빈 파일/크기 상한 → 내용 시그니처.
    """
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
    validate_image_signature(data)
    return data
