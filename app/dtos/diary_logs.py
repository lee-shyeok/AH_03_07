from datetime import date, datetime
from uuid import UUID

from asyncmy.converters import Decimal
from pydantic import BaseModel

from app.models.diary_symptom_logs import OverallCondition


class SymptomLogCreateRequest(BaseModel):
    log_date: date
    overall_condition: OverallCondition
    body_parts: list[str] | None = None
    feeling: dict | None = None
    memo: str | None = None


class SymptomLogResponse(BaseModel):
    id: UUID
    log_date: date
    overall_condition: OverallCondition
    body_parts: list[str] | None
    feeling: dict | None
    memo: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SymptomLogListResponse(BaseModel):
    logs: list[SymptomLogResponse]
    total: int


class MedicationLogCreateRequest(BaseModel):
    log_date: date
    drug_name: str
    taken: bool = True
    taken_time: datetime | None = None
    notes: str | None = None
    # NOTI-008: 위치 태깅 (옵셔널)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class MedicationLogResponse(BaseModel):
    id: UUID
    log_date: date
    drug_name: str
    taken: bool
    taken_time: datetime | None
    notes: str | None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_recorded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicationLogListResponse(BaseModel):
    logs: list[MedicationLogResponse]
    total: int
