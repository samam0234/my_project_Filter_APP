"""Request / parsed-prompt schemas."""

from typing import List

from pydantic import BaseModel, Field


class ParsedPrompt(BaseModel):
    """Structured result of natural-language prompt analysis."""

    target: List[str] = Field(default_factory=lambda: ["person"])
    effect: str = Field(default="remove_bg")  # remove_bg | blur | crop | none
    intensity: int = Field(default=15, ge=0, le=100)
    crop: bool = False


class UploadFormMeta(BaseModel):
    """Optional metadata accompanying multipart upload."""

    prompt: str = Field(..., min_length=1, max_length=1000)
