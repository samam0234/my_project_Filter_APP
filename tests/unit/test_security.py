# -*- coding: utf-8 -*-
"""업로드 확장자·MIME 검증.

security.validate_* 가 허용/거부 목록을 지키는지 확인.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic_settings")

from app.core.security import validate_extension, validate_mime
from app.exceptions import FileValidationError


def test_validate_extension_ok():
    """jpg/png 허용."""
    assert validate_extension("a.jpg") == ".jpg"
    assert validate_extension("b.PNG") == ".png"


def test_validate_extension_bad():
    """gif / None 거부."""
    with pytest.raises(FileValidationError):
        validate_extension("x.gif")
    with pytest.raises(FileValidationError):
        validate_extension(None)


def test_validate_mime_ok():
    """image/jpeg 허용."""
    mime = validate_mime("image/jpeg")
    assert mime == "image/jpeg"


def test_validate_mime_bad():
    """pdf 등 비이미지 MIME 거부."""
    with pytest.raises(FileValidationError):
        validate_mime("application/pdf")
