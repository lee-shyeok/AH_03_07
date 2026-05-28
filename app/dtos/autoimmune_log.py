from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.symptom_check_log import SymptomCode


class ActivityLogUpsertRequest(BaseModel):
    pain_vas: int = Field(..., ge=0, le=10)
    fatigue: int = Field(..., ge=0, le=10)
    morning_stiffness_min: int | None = Field(None, ge=0)
    joint_swelling_areas: list[str] | None = None
    daily_difficulty: int = Field(..., ge=0, le=10)
    note: str | None = Field(None, max_length=500)


class ActivityLogResponse(BaseSerializerModel):
    id: int
    log_date: date
    pain_vas: int
    fatigue: int
    morning_stiffness_min: int | None
    joint_swelling_areas: list[str] | None
    daily_difficulty: int
    note: str | None
    created_at: datetime
    updated_at: datetime


class SymptomCheckCreateRequest(BaseModel):
    checked_symptoms: list[SymptomCode]


class SymptomCheckResponse(BaseSerializerModel):
    id: int
    checked_symptoms: list[SymptomCode]
    red_flag_triggered: bool
    red_flag_symptoms: list[SymptomCode] = []
    created_at: datetime
