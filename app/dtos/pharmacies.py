from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PharmacyCreateRequest(BaseModel):
    name: str
    address: str
    phone: str | None = None
    latitude: Decimal
    longitude: Decimal
    operating_hours: dict | None = None
    is_24h_available: bool = False
    is_holiday_available: bool = False


class PharmacyResponse(BaseModel):
    id: UUID
    name: str
    address: str
    phone: str | None
    latitude: Decimal
    longitude: Decimal
    operating_hours: dict | None
    is_24h_available: bool
    is_holiday_available: bool

    class Config:
        from_attributes = True


class PharmacyListResponse(BaseModel):
    pharmacies: list[PharmacyResponse]
    total: int
