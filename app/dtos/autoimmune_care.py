from __future__ import annotations

from pydantic import BaseModel

from app.models.user_medication import DrugClass
from app.models.user_risk_profile import PregnancyStatus


class SourceLink(BaseModel):
    name: str
    url: str


class MedicationCard(BaseModel):
    medication_id: int
    name: str
    drug_class: DrugClass
    is_injection: bool
    user_note: str | None
    discontinuation_notice: str
    consultation_checklist: list[str]
    official_source_url: str
    reference_sources: list[SourceLink]
    autoimmune_notes: list[str] = []


class MedicationCardListResponse(BaseModel):
    cards: list[MedicationCard]


class PregnancySafetyResponse(BaseModel):
    applicable: bool
    pregnancy_status: PregnancyStatus
    consultation_notice: str | None
    general_safety_info: list[str] | None
    disclaimer: str | None


class VaccineInfoItem(BaseModel):
    name: str
    description: str


class VaccinePreventionResponse(BaseModel):
    recommended_vaccines: list[VaccineInfoItem]
    live_vaccine_caution: str
    infection_prevention_tips: list[str]
    disclaimer: str
