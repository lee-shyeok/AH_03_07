from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel

from app.models.notifications import NotificationType


class NotificationSettingUpdateRequest(BaseModel):
    medication_enabled: bool | None = None
    diary_enabled: bool | None = None
    health_metric_enabled: bool | None = None
    emergency_enabled: bool | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class NotificationSettingResponse(BaseModel):
    id: UUID
    medication_enabled: bool
    diary_enabled: bool
    health_metric_enabled: bool
    emergency_enabled: bool
    quiet_hours_start: time | None
    quiet_hours_end: time | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: NotificationType
    title: str
    content: str
    is_read: bool
    scheduled_at: datetime
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
