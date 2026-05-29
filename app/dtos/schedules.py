from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.favorite_places import PlaceType


class AppointmentCreateRequest(BaseModel):
    appointment_date: datetime
    hospital_name: str
    doctor_name: str | None = None
    purpose: str | None = None
    notes: str | None = None
    notification_enabled: bool = True


class AppointmentResponse(BaseModel):
    id: UUID
    appointment_date: datetime
    hospital_name: str
    doctor_name: str | None
    purpose: str | None
    notes: str | None
    notification_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    appointments: list[AppointmentResponse]
    total: int


class FavoritePlaceCreateRequest(BaseModel):
    place_type: PlaceType
    name: str
    address: str | None = None
    phone: str | None = None
    memo: str | None = None


class FavoritePlaceResponse(BaseModel):
    id: UUID
    place_type: PlaceType
    name: str
    address: str | None
    phone: str | None
    memo: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FavoritePlaceListResponse(BaseModel):
    places: list[FavoritePlaceResponse]
    total: int
