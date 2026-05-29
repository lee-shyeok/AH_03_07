from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.content_conversions import ConversionStatus, ConversionType


class CardNewsCreateRequest(BaseModel):
    guide_id: UUID


class ContentConversionResponse(BaseModel):
    id: UUID
    guide_id: UUID
    conversion_type: ConversionType
    status: ConversionStatus
    file_url: str | None
    file_urls: list[str] | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
