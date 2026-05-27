from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.medical_schedule import MedicalScheduleType


class MedicalScheduleCreateRequest(BaseModel):
    schedule_type: MedicalScheduleType
    scheduled_date: date
    note: str | None = Field(None, max_length=500)


class MedicalScheduleUpdateRequest(BaseModel):
    schedule_type: MedicalScheduleType | None = None
    scheduled_date: date | None = None
    note: str | None = Field(None, max_length=500)


class MedicalScheduleResponse(BaseSerializerModel):
    id: int
    schedule_type: MedicalScheduleType
    scheduled_date: date
    note: str | None
    created_at: datetime
    updated_at: datetime


class LabResultCreateRequest(BaseModel):
    test_date: date
    test_item: str = Field(..., min_length=1, max_length=128)
    value: str = Field(..., min_length=1, max_length=64)
    reference_range: str | None = Field(None, max_length=64)
    note: str | None = Field(None, max_length=500)


class LabResultUpdateRequest(BaseModel):
    test_date: date | None = None
    test_item: str | None = Field(None, min_length=1, max_length=128)
    value: str | None = Field(None, min_length=1, max_length=64)
    reference_range: str | None = Field(None, max_length=64)
    note: str | None = Field(None, max_length=500)


class LabResultResponse(BaseSerializerModel):
    id: int
    test_date: date
    test_item: str
    value: str
    reference_range: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime
