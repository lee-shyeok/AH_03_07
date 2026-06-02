from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.medical_schedule import MedicalScheduleType


class MedicalScheduleCreateRequest(BaseModel):
    schedule_type: MedicalScheduleType
    title: str = Field(..., max_length=200)
    scheduled_date: date
    reminder_days_before: int = Field(default=1, ge=1, le=30)
    note: str | None = Field(None, max_length=500)


class MedicalScheduleUpdateRequest(BaseModel):
    schedule_type: MedicalScheduleType
    title: str = Field(..., max_length=200)
    scheduled_date: date
    reminder_days_before: int = Field(default=1, ge=1, le=30)
    note: str | None = Field(None, max_length=500)


class MedicalScheduleResponse(BaseSerializerModel):
    id: int
    schedule_type: MedicalScheduleType
    title: str | None
    scheduled_date: date
    reminder_days_before: int
    note: str | None
    created_at: datetime
    updated_at: datetime


class LabResultCreateRequest(BaseModel):
    test_date: date
    test_type: str = Field(..., min_length=1, max_length=128)
    user_recorded_value: str = Field(..., min_length=1, max_length=64)
    reference_range: str | None = Field(None, max_length=64)
    note: str | None = Field(None, max_length=500)


class LabResultUpdateRequest(BaseModel):
    test_date: date | None = None
    test_type: str | None = Field(None, min_length=1, max_length=128)
    user_recorded_value: str | None = Field(None, min_length=1, max_length=64)
    reference_range: str | None = Field(None, max_length=64)
    note: str | None = Field(None, max_length=500)


class LabResultResponse(BaseSerializerModel):
    id: int
    test_date: date
    test_type: str = Field(validation_alias="test_item")
    user_recorded_value: str = Field(validation_alias="value")
    reference_range: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime
