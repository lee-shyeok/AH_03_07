from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.health_guides import GuideStatus, GuideType


class HealthGuideCreateRequest(BaseModel):
    guide_type: GuideType
    user_question: str


class HealthGuideResponse(BaseModel):
    id: UUID
    guide_type: GuideType
    status: GuideStatus
    user_question: str
    guide_content: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthGuideListResponse(BaseModel):
    guides: list[HealthGuideResponse]
    total: int
