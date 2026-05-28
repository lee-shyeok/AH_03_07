from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.activity_alert_setting import AlertCriterion


class ChartPeriod(StrEnum):
    WEEK = "1w"
    MONTH = "1m"
    QUARTER = "3m"


class ActivityChartPoint(BaseModel):
    log_date: date
    pain_vas: int
    fatigue: int


class MetricStats(BaseModel):
    avg: float | None
    max: int | None
    min: int | None


class ActivityChartResponse(BaseModel):
    period: ChartPeriod
    start_date: date
    end_date: date
    series: list[ActivityChartPoint]
    pain_stats: MetricStats
    fatigue_stats: MetricStats


class AlertSettingUpsertRequest(BaseModel):
    pain_threshold: int | None = Field(None, ge=0, le=10)
    pain_consecutive_days: int | None = Field(None, ge=1)
    morning_stiffness_threshold: int | None = Field(None, ge=0)
    fatigue_threshold: int | None = Field(None, ge=0, le=10)
    alert_message: str = Field(..., min_length=1, max_length=500)
    is_enabled: bool = True


class AlertSettingResponse(BaseSerializerModel):
    id: int
    pain_threshold: int | None
    pain_consecutive_days: int | None
    morning_stiffness_threshold: int | None
    fatigue_threshold: int | None
    alert_message: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class AlertStatusResponse(BaseModel):
    is_enabled: bool
    triggered: bool
    triggered_criteria: list[AlertCriterion]
    alert_message: str | None
    disclaimer: str | None


class AlertTemplatesResponse(BaseModel):
    templates: list[str]
