from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.feedback_logs import FeedbackType, TargetType


class FeedbackCreateRequest(BaseModel):
    target_type: TargetType
    target_id: UUID
    feedback_type: FeedbackType
    rating: int | None = None
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    target_type: TargetType
    target_id: UUID
    feedback_type: FeedbackType
    rating: int | None
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    feedbacks: list[FeedbackResponse]
    total: int
