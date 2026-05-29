from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.share_links import ShareDuration


class GuardianCreateRequest(BaseModel):
    name: str
    phone_number: str | None = None
    email: str | None = None
    relationship: str | None = None


class GuardianResponse(BaseModel):
    id: UUID
    name: str
    phone_number: str | None
    email: str | None
    relationship: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GuardianListResponse(BaseModel):
    guardians: list[GuardianResponse]
    total: int


class ShareLinkCreateRequest(BaseModel):
    guardian_id: UUID
    duration: ShareDuration
    categories: list[str]
    include_summary_only: bool = True


class ShareLinkResponse(BaseModel):
    id: UUID
    guardian_id: UUID
    token: str
    duration: ShareDuration
    categories: list[str]
    include_summary_only: bool
    expires_at: datetime
    is_revoked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ShareLinkListResponse(BaseModel):
    share_links: list[ShareLinkResponse]
    total: int


class ShareLogResponse(BaseModel):
    id: UUID
    viewed_at: datetime
    viewer_ip: str | None

    class Config:
        from_attributes = True
