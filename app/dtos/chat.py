from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

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
    # API 명세서 /sources 네이밍과 일관성 유지 (REQ-KB-003)
    model_config = ConfigDict(extra="ignore")  # 구 DB 레코드(title/url 키) 역호환

    source_title: str | None = None
    source_org: str | None = None
    source_url: str | None = None  # KB payload에 url 없음 → None 고정, 적재 시 추가 예정
    source_page: int | None = None
    published_year: int | None = None
    section_title: str | None = None  # 챕터명 (REQ-KB-003 "문서명+챕터")
    snippet: str | None = None


class MessageResponse(BaseModel):
    message_id: int
    role: MessageRole
    content: str
    rag_sources: list[RagSource]
    blocked_by_filter: bool
    block_reason: str | None = None

    @field_serializer("role")
    def serialize_role(self, role: MessageRole) -> str:
        return role.value.lower()


class MessageItem(BaseModel):
    id: int
    role: MessageRole
    content: str
    rag_sources: list[RagSource]
    blocked_by_filter: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("role")
    def serialize_role(self, role: MessageRole) -> str:
        return role.value.lower()


class MessageHistoryResponse(BaseModel):
    messages: list[MessageItem]
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
