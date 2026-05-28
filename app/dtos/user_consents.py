from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.user_consents import ConsentType


class ConsentCreateRequest(BaseModel):
    consent_type: ConsentType
    agreed: bool
    version: str


class ConsentResponse(BaseModel):
    id: UUID
    consent_type: ConsentType
    agreed: bool
    version: str
    agreed_at: datetime

    class Config:
        from_attributes = True


class ConsentListResponse(BaseModel):
    consents: list[ConsentResponse]
    total: int
