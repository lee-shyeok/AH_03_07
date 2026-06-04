from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.emergency_cards import SirenMode


class EmergencyCardCreateRequest(BaseModel):
    blood_type: str | None = None
    allergies: str | None = None
    chronic_conditions: str | None = None
    emergency_contacts: list[dict] | None = None
    siren_mode: SirenMode = SirenMode.NORMAL


class EmergencyCardResponse(BaseModel):
    id: UUID
    blood_type: str | None
    allergies: str | None
    chronic_conditions: str | None
    emergency_contacts: list[dict] | None
    siren_mode: SirenMode
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SOSTriggerRequest(BaseModel):
    latitude: float
    longitude: float


class SOSTriggerResponse(BaseModel):
    status: str
    notified_count: int
    latitude: float
    longitude: float
