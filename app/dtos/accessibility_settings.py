from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.accessibility_settings import FontSize


class AccessibilitySettingUpdateRequest(BaseModel):
    font_size: FontSize | None = None
    tts_enabled: bool | None = None
    easy_language: bool | None = None
    guardian_share_enabled: bool | None = None


class AccessibilitySettingResponse(BaseModel):
    id: UUID
    font_size: FontSize
    tts_enabled: bool
    easy_language: bool
    guardian_share_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
