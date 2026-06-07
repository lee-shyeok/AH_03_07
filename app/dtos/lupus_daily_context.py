from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.lupus_daily_context import StressLevel


class LupusDailyContextUpsertRequest(BaseModel):
    log_date: date
    uv_exposure_minutes: int | None = Field(None, ge=0)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    stress_level: StressLevel | None = None
    med_taken: bool | None = None
    note: str | None = Field(None, max_length=500)


class LupusDailyContextResponse(BaseSerializerModel):
    id: int
    log_date: date
    uv_exposure_minutes: int | None
    sleep_hours: float | None
    stress_level: StressLevel | None
    med_taken: bool | None
    note: str | None
    created_at: datetime
    updated_at: datetime
