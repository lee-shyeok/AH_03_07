from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.chat_message import MessageRole


class SessionStartResponse(BaseModel):
    session_id: int


class MessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("content must be at least 1 character")
        if len(v) > 4000:
            raise ValueError("content must be at most 4000 characters")
        return v


class RagSource(BaseModel):
    title: str
    url: str | None = None
    snippet: str | None = None


class MessageResponse(BaseModel):
    content: str
    rag_sources: list[RagSource]
    blocked_by_filter: bool
    block_reason: str | None


class MessageItem(BaseModel):
    id: int
    role: MessageRole
    content: str
    rag_sources: list[RagSource]
    blocked_by_filter: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    items: list[MessageItem]
    total: int
    page: int
    size: int


class FeedbackRequest(BaseModel):
    score: int
    comment: str | None = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("score must be +1 or -1")
        return v


class FeedbackResponse(BaseModel):
    message_id: int
    score: int
    recorded_at: datetime
