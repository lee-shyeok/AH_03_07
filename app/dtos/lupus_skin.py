from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel
from app.models.lupus_skin_log import LupusSkinSymptomType


class LupusSkinLogCreateRequest(BaseModel):
    symptom_type: LupusSkinSymptomType
    log_date: date
    note: str | None = None


class LupusSkinLogUpdateRequest(BaseModel):
    symptom_type: LupusSkinSymptomType | None = None
    log_date: date | None = None
    note: str | None = None


class LupusSkinLogResponse(BaseSerializerModel):
    id: int
    symptom_type: LupusSkinSymptomType
    log_date: date
    note: str | None
    created_at: datetime
    updated_at: datetime
