from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.symptom_check_log import SymptomCode


class ActivityLogUpsertRequest(BaseModel):
    log_date: date
    pain_vas: int = Field(..., ge=0, le=10)
    fatigue: int = Field(..., ge=0, le=10)
    morning_stiffness_minutes: int | None = Field(None, ge=0)
    joint_swelling_areas: list[str] | None = None
    daily_difficulty: int = Field(..., ge=0, le=10)
    free_memo: str | None = Field(None, max_length=500)


class ActivityLogResponse(BaseSerializerModel):
    id: int
    log_date: date
    pain_vas: int
    fatigue: int
    morning_stiffness_minutes: int | None = Field(None, validation_alias="morning_stiffness_min")
    joint_swelling_areas: list[str] | None
    daily_difficulty: int
    free_memo: str | None = Field(None, validation_alias="note")
    created_at: datetime
    updated_at: datetime


class SymptomCheckCreateRequest(BaseModel):
    checked_symptoms: list[SymptomCode]


class SymptomCheckResponse(BaseSerializerModel):
    id: int
    checked_symptoms: list[SymptomCode]
    red_flag_triggered: bool
    red_flag_symptoms: list[SymptomCode] = []
    risk_flag_ids: list[int] = []
    created_at: datetime
