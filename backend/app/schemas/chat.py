"""AI 채팅 요청 · 응답 스키마."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=20_000)  # 서버가 CHAT_MAX_CHARS 로 다시 자른다


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=100)
    llm_model: Optional[str] = Field(default=None, max_length=100)  # 안 보내면 서버 기본 모델


class ChatResponse(BaseModel):
    reply: str
    model: str
    elapsed_ms: int
