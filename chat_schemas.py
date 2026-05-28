from datetime import datetime

from pydantic import BaseModel, field_validator

# ── 세션 ─────────────────────────────────────────────────


class ChatSessionResponse(BaseModel):
    id: int
    is_active: bool
    created_at: datetime
    last_activity_at: datetime
    ended_at: datetime | None = None

    class Config:
        from_attributes = True


class ChatSessionListItem(BaseModel):
    id: int
    is_active: bool
    first_message: str | None = None  # 첫 질문 (앞 50자)
    message_count: int
    created_at: datetime


class ChatSessionListResponse(BaseModel):
    items: list[ChatSessionListItem]
    total: int
    page: int
    size: int


# ── 메시지 ────────────────────────────────────────────────


class ChatMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_valid(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("메시지를 입력해주세요.")
        if len(stripped) > 2000:
            raise ValueError("메시지는 2000자 이하여야 합니다.")
        return stripped


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: int
    messages: list[ChatMessageResponse]
    total: int
    page: int
    size: int


# ── 피드백 ────────────────────────────────────────────────


class ChatFeedbackRequest(BaseModel):
    is_positive: bool
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def comment_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("코멘트는 500자 이하여야 합니다.")
        return v


class ChatFeedbackResponse(BaseModel):
    id: int
    message_id: int
    is_positive: bool
    comment: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
