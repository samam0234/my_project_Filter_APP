"""요청·구조화 프롬프트 스키마 (Pydantic)."""

from typing import List

from pydantic import BaseModel, Field


class ParsedPrompt(BaseModel):
    """자연어 프롬프트 분석 결과 구조체."""

    target: List[str] = Field(default_factory=lambda: ["person"])
    effect: str = Field(default="remove_bg")  # remove_bg | blur | crop | none
    intensity: int = Field(default=15, ge=0, le=100)
    crop: bool = False


class UploadFormMeta(BaseModel):
    """multipart 업로드 부가 메타데이터."""

    prompt: str = Field(..., min_length=1, max_length=1000)
