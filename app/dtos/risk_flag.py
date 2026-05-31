from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.dtos.base import BaseSerializerModel
from app.models.risk_flag import RiskFlagSourceType, RiskFlagStatus


class RiskFlagItem(BaseSerializerModel):
    id: int
    source_type: RiskFlagSourceType
    source_id: int | None
    flag_code: str
    flag_label: str
    category: str
    message: str
    red_flag: bool
    consultation_recommended: bool
    status: RiskFlagStatus
    created_at: datetime


class RiskFlagStatusUpdateRequest(BaseModel):
    status: RiskFlagStatus

    @field_validator("status")
    @classmethod
    def only_resolved_or_dismissed(cls, v: RiskFlagStatus) -> RiskFlagStatus:
        if v not in (RiskFlagStatus.RESOLVED, RiskFlagStatus.DISMISSED):
            raise ValueError("status는 RESOLVED 또는 DISMISSED만 허용됩니다")
        return v
