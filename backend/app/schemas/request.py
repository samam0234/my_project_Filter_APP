"""요청·구조화 프롬프트 스키마 (Pydantic).

API multipart 폼과 LangGraph 노드 사이에서 오가는
공통 구조체 정의.
"""

from typing import List

from pydantic import BaseModel, Field


class ParsedPrompt(BaseModel):
    """자연어 프롬프트 분석 결과 구조체.

    prompt_analyzer 휴리스틱(또는 이후 LLM)이 채운다.
      target    : 남길 대상 클래스 목록 (예: ["person", "dog"])
      effect    : remove_bg | blur | crop | none
      intensity : 블러 강도 등 0~100
      crop      : 주 효과 후 추가 크롭 여부
    """

    target: List[str] = Field(default_factory=lambda: ["person"])
    effect: str = Field(default="remove_bg")  # remove_bg | blur | crop | none
    intensity: int = Field(default=15, ge=0, le=100)
    crop: bool = False


class UploadFormMeta(BaseModel):
    """multipart 업로드 부가 메타데이터 (문서/검증용)."""

    prompt: str = Field(..., min_length=1, max_length=1000)
