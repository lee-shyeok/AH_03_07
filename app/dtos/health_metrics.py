from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.health_metrics import MetricType


class HealthMetricCreateRequest(BaseModel):
    metric_type: MetricType
    user_recorded_value: str
    diastolic_value: str | None = None
    measured_at: datetime
    notes: str | None = None


class HealthMetricResponse(BaseModel):
    id: UUID
    metric_type: MetricType
    user_recorded_value: Decimal
    diastolic_value: Decimal | None
    measured_at: datetime
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class HealthMetricListResponse(BaseModel):
    metrics: list[HealthMetricResponse]
    total: int
