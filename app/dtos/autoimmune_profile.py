from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.user_medication import DrugClass
from app.models.user_risk_profile import PregnancyStatus


class RiskProfileUpsertRequest(BaseModel):
    pregnancy_status: PregnancyStatus = PregnancyStatus.NONE
    renal_impairment: bool = False
    hepatic_impairment: bool = False
    infection_history: str | None = Field(None, max_length=1000)
    drug_allergy: str | None = Field(None, max_length=1000)
    comorbidities: str | None = Field(None, max_length=1000)


class RiskProfileResponse(BaseSerializerModel):
    id: int
    pregnancy_status: PregnancyStatus
    renal_impairment: bool
    hepatic_impairment: bool
    infection_history: str | None
    drug_allergy: str | None
    comorbidities: str | None
    updated_at: datetime


class MedicationCreateItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    drug_class: DrugClass
    is_injection: bool = False
    note: str | None = Field(None, max_length=500)


class MedicationBulkCreateRequest(BaseModel):
    medications: list[MedicationCreateItem] = Field(..., min_length=1)


class MedicationUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    drug_class: DrugClass | None = None
    is_injection: bool | None = None
    note: str | None = Field(None, max_length=500)


class MedicationResponse(BaseSerializerModel):
    id: int
    name: str
    drug_class: DrugClass
    is_injection: bool
    note: str | None
    created_at: datetime
